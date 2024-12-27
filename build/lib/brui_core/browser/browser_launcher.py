import os
import sys
import subprocess
import socket
import asyncio
import time
import logging
from typing import Optional, Set, NamedTuple

# Assuming `brui_core.config.config_parser` modules are available
# If not, you may need to implement or mock these modules
from brui_core.config.config_parser import EnvironmentConfigParser, TOMLConfigParser

logger = logging.getLogger(__name__)


class ChromeProcess(NamedTuple):
    pid: int
    ppid: int
    cmd: str


def get_chrome_startup_path() -> str:
    """
    Returns the appropriate Chrome startup path based on the operating system.
    """
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform == "linux":
        return "/usr/bin/google-chrome"
    elif sys.platform == "win32":
        # Common Chrome installation paths on Windows
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        raise FileNotFoundError("Chrome executable not found in standard locations")
    raise Exception(
        "Unsupported OS. This script supports Windows, Linux, and macOS only."
    )


def get_chrome_process_path() -> str:
    """
    Returns the path to match against running Chrome processes.
    """
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif sys.platform == "linux":
        return "/opt/google/chrome/chrome"
    elif sys.platform == "win32":
        return "chrome.exe"
    raise Exception(
        "Unsupported OS. This script supports Windows, Linux, and macOS only."
    )


def get_chrome_pids() -> Set[ChromeProcess]:
    """
    Get all Chrome process PIDs using platform-specific commands.
    """
    try:
        chrome_path = get_chrome_process_path()
        chrome_processes = set()

        if sys.platform == "win32":
            import wmi

            w = wmi.WMI()
            for process in w.Win32_Process(name="chrome.exe"):
                chrome_processes.add(
                    ChromeProcess(
                        pid=process.ProcessId,
                        ppid=process.ParentProcessId,
                        cmd=process.CommandLine or "",
                    )
                )
        else:
            # Linux/macOS implementation

            if sys.platform == "darwin":
                cmd = ["ps", "-ax", "-o", "pid=,ppid=,command="]

            else:
                cmd = ["ps", "-eo", "pid=,ppid=,cmd="]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"Failed to get process list: {result.stderr}")
                return set()

            for line in result.stdout.splitlines():
                try:
                    parts = line.strip().split(maxsplit=2)
                    if len(parts) == 3:
                        pid, ppid, command = parts
                        if chrome_path in command:
                            chrome_processes.add(
                                ChromeProcess(pid=int(pid), ppid=int(ppid), cmd=command)
                            )
                except (ValueError, IndexError) as e:
                    logger.debug(f"Error processing process info: {e}")
                    continue

        return chrome_processes
    except Exception as e:
        logger.error(f"Error getting Chrome processes: {e}")
        return set()


def find_main_chrome_parent(processes: Set[ChromeProcess]) -> Optional[ChromeProcess]:
    """
    Find the main Chrome parent process that spawned other Chrome processes.
    Returns the ChromeProcess object for the main parent, or None if not found.
    """
    if not processes:
        return None

    # Create mapping of pid to process
    pid_to_process = {p.pid: p for p in processes}

    # Find processes whose parent is also a Chrome process
    child_processes = {p for p in processes if p.ppid in pid_to_process}

    # The main Chrome process should be a parent but not a child
    parent_candidates = processes - child_processes

    if not parent_candidates:
        return None

    # If multiple candidates, choose the one with the shortest command
    # (usually the main browser process has fewer arguments)
    return min(parent_candidates, key=lambda p: len(p.cmd))


def wait_for_process_termination(pid: int, timeout: int = 5) -> bool:
    """
    Wait for a process to terminate completely.
    Returns True if process terminated, False if timeout occurred.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        try:
            os.kill(pid, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            return True
        except Exception as e:
            logger.error(f"Error checking process {pid}: {e}")
            return False
    return False


def kill_all_chrome_processes():
    """
    Enhanced function to kill Chrome processes by targeting the main parent first.
    """
    try:
        # Get all Chrome processes
        chrome_processes = get_chrome_pids()

        if not chrome_processes:
            logger.info("No Chrome processes found to kill")
            return

        logger.info(f"Found Chrome processes: {chrome_processes}")

        # Find and kill the main parent process first
        main_parent = find_main_chrome_parent(chrome_processes)
        if main_parent:
            logger.info(f"Killing main Chrome parent process: {main_parent}")
            try:
                os.kill(main_parent.pid, 15)  # SIGTERM
                if not wait_for_process_termination(main_parent.pid, timeout=5):
                    try:
                        os.kill(main_parent.pid, 9)  # SIGKILL
                    except PermissionError as e:
                        logger.error(
                            f"Permission denied when trying to kill process {main_parent.pid}: {e}"
                        )
            except ProcessLookupError:
                pass

        # Check for remaining processes and force kill them
        remaining_processes = get_chrome_pids()
        if remaining_processes:
            logger.info(f"Killing remaining Chrome processes: {remaining_processes}")
            for process in remaining_processes:
                try:
                    os.kill(process.pid, 9)  # SIGKILL
                except ProcessLookupError:
                    continue

        # Final verification
        final_check = get_chrome_pids()
        if final_check:
            raise Exception(f"Failed to terminate Chrome processes: {final_check}")

        logger.info("Successfully terminated all Chrome processes")
    except Exception as e:
        logger.error(f"Error during Chrome process termination: {e}")
        raise


async def is_browser_opened_in_debug_mode():
    """
    Check if the browser is opened in debug mode by attempting to connect to the debug port.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((remote_host, remote_debugging_port))
            return result == 0
    except (ConnectionRefusedError, OSError) as error:
        logger.error(f"Debug mode check error: {error}")
        return False


async def wait_for_browser_start(timeout=20, retry_interval=1):
    """
    Wait for the browser to start and listen on the debug port.

    Args:
        timeout (int): Maximum time to wait in seconds
        retry_interval (int): Time between retry attempts in seconds

    Raises:
        TimeoutError: If browser doesn't start within timeout period
    """
    start_time = asyncio.get_event_loop().time()

    while not await is_browser_opened_in_debug_mode():
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(
                f"Timed out waiting for port {remote_debugging_port} to listen"
            )
        await asyncio.sleep(retry_interval)


async def launch_browser(timeout=20):
    """
    Launches a new instance of Chrome in debug mode.
    Before launching, it assumes that any necessary cleanup (like killing existing Chrome processes)
    has already been performed if needed.

    :param timeout: Maximum time to wait for the browser to start in seconds.
    """
    executable_path = get_chrome_startup_path()

    # Construct the user data directory path
    user_data_dir = os.path.join(os.getcwd(), "ChromeDebugUserData")
    os.makedirs(user_data_dir, exist_ok=True)

    # Browser launch arguments
    args = [
        executable_path,
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        f"--remote-debugging-port={remote_debugging_port}",
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={chrome_profile_directory}",
    ]

    # Launch Chrome in debug mode
    subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"Chrome launched in debug mode on port {remote_debugging_port}.")

    # Wait for Chrome to start and listen on the debug port
    await wait_for_browser_start(timeout=timeout)


def get_browser_config():
    """
    Retrieve browser configuration from environment variables or config file.
    """
    if "BROWSER_CONFIG_PATH" in os.environ:
        config_parser = EnvironmentConfigParser("BROWSER_CONFIG_PATH")
        browser_config = config_parser.parse()
    else:
        current_file = os.path.realpath(__file__)
        config_file = os.path.join(os.path.dirname(current_file), "config.toml")
        config_parser = TOMLConfigParser()
        browser_config = config_parser.parse(config_file)

    # Override chrome_profile_directory if CHROME_PROFILE_DIRECTORY environment variable is set
    if "CHROME_PROFILE_DIRECTORY" in os.environ:
        browser_config["browser"]["chrome_profile_directory"] = os.environ[
            "CHROME_PROFILE_DIRECTORY"
        ]

    # Override download_directory if CHROME_DOWNLOAD_DIRECTORY environment variable is set
    if "CHROME_DOWNLOAD_DIRECTORY" in os.environ:
        browser_config["browser"]["download_directory"] = os.environ[
            "CHROME_DOWNLOAD_DIRECTORY"
        ]

    # Ensure remote_debugging_port and remote_host are integers and strings
    browser_config["browser"]["remote_debugging_port"] = int(
        browser_config.get("browser", {}).get("remote_debugging_port", 9222)
    )
    browser_config["browser"]["remote_host"] = browser_config.get("browser", {}).get(
        "remote_host", "localhost"
    )

    return browser_config


# Load browser configuration
browser_config = get_browser_config()

chrome_profile_directory = browser_config.get("browser", {}).get(
    "chrome_profile_directory", "Default"
)
remote_debugging_port = browser_config.get("browser", {}).get(
    "remote_debugging_port", 9222
)
remote_host = browser_config.get("browser", {}).get("remote_host", "localhost")


# Main execution function
async def main():
    try:
        # Kill existing Chrome processes
        kill_all_chrome_processes()

        # Launch Chrome in debug mode
        await launch_browser()

        logger.info("Browser launched successfully in debug mode.")

        # Here you can include additional logic to interact with the browser
        # For example, send commands via the DevTools Protocol

    except Exception as e:
        logger.error(f"An error occurred: {e}")


# Run the main function
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
