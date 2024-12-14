import os
import sys
import subprocess
import socket
import asyncio

from brui_core.config.config_parser import EnvironmentConfigParser, TOMLConfigParser

# Function to launch the browser based on the operating system
async def launch_browser():
    if sys.platform == 'linux':
        executable_path = '/usr/bin/google-chrome' 
    elif sys.platform == 'darwin':  # macOS
        executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    else:
        raise Exception("Unsupported OS. This script supports Linux and macOS only.")

    # Browser launch arguments
    args = [
        "--no-first-run",
        "--flag-switches-begin",
        "--flag-switches-end",
        f"--remote-debugging-port={remote_debugging_port}",
        f"--profile-directory={chrome_profile_directory}"
    ]

    subprocess.Popen([executable_path] + args)
    await wait_for_browser_start()

# Check if the browser is opened in debug mode
async def is_browser_opened_in_debug_mode():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((remote_host, remote_debugging_port))
            return result == 0
    except (ConnectionRefusedError, OSError) as error:
        print(f"Debug mode check error: {error}")
        return False

# Function to wait for the browser to start
async def wait_for_browser_start(timeout=20, retry_interval=1):
    start_time = asyncio.get_event_loop().time()
    while not await is_browser_opened_in_debug_mode():
        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Timed out waiting for port {remote_debugging_port} to listen")
        await asyncio.sleep(retry_interval)

# Retrieve browser configuration
def get_browser_config():
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
        browser_config["browser"]["chrome_profile_directory"] = os.environ["CHROME_PROFILE_DIRECTORY"]
    
    # Override download_directory if CHROME_DOWNLOAD_DIRECTORY environment variable is set
    if "CHROME_DOWNLOAD_DIRECTORY" in os.environ:
        browser_config["browser"]["download_directory"] = os.environ["CHROME_DOWNLOAD_DIRECTORY"]
    
    return browser_config

# Load browser configuration
browser_config = get_browser_config()

chrome_profile_directory = browser_config.get("browser", {}).get("chrome_profile_directory", "Default")
remote_debugging_port = browser_config.get("browser", {}).get("remote_debugging_port", 9222)
remote_host = browser_config.get("browser", {}).get("remote_host", "localhost")