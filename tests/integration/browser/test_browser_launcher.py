import pytest
import asyncio
import os
import socket
import time
from pathlib import Path
from unittest.mock import patch

from brui_core.browser.browser_launcher import (
    launch_browser,
    kill_all_chrome_processes,
    is_browser_opened_in_debug_mode,
    get_browser_config,
    get_chrome_pids,
)


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """Set up test environment variables"""
    # Chrome requires a user data dir for remote debugging
    user_data_dir = tmp_path / "chrome_user_data"
    os.environ['CHROME_USER_DATA_DIR'] = str(user_data_dir)
    yield
    if 'CHROME_USER_DATA_DIR' in os.environ:
        del os.environ['CHROME_USER_DATA_DIR']


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    """Ensure clean state before and after tests by killing all Chrome processes"""
    kill_all_chrome_processes()
    yield
    kill_all_chrome_processes()


def is_port_in_use(port):
    """Check if a port is actually in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


@pytest.mark.asyncio
async def test_launch_and_kill_browser_flow():
    """Test the complete flow of launching and killing Chrome"""
    # Verify no Chrome processes at start
    assert not get_chrome_pids(), "Chrome processes found before test"
    assert not await is_browser_opened_in_debug_mode(), "Debug port should not be open"

    # Launch browser
    await launch_browser()

    # Verify Chrome is running
    chrome_processes = get_chrome_pids()
    assert chrome_processes, "No Chrome processes found after launch"

    # Verify debug port is listening
    port = get_browser_config()["browser"]["remote_debugging_port"]
    assert await is_browser_opened_in_debug_mode(), "Debug port not open after launch"
    assert is_port_in_use(port), "Debug port not actually listening"

    # Kill browser
    kill_all_chrome_processes()

    # Verify cleanup
    assert not get_chrome_pids(), "Chrome processes still running after kill"
    assert not await is_browser_opened_in_debug_mode(), "Debug port still open after kill"
    assert not is_port_in_use(port), "Debug port still in use"


@pytest.mark.asyncio
async def test_multiple_launch_attempts():
    """Test launching browser multiple times"""
    # First launch
    await launch_browser()

    # Allow some time for Chrome to start
    await asyncio.sleep(5)

    initial_processes = get_chrome_pids()
    assert initial_processes, "First launch failed"

    # Capture the number of Chrome processes
    initial_count = len(initial_processes)

    # Try second launch without killing
    await launch_browser()

    # Allow some time for potential additional processes
    await asyncio.sleep(5)

    new_processes = get_chrome_pids()
    new_count = len(new_processes)

    # Should not create additional processes
    assert new_count == initial_count, "Multiple launches created extra processes"

    # Debug port should still be accessible
    assert await is_browser_opened_in_debug_mode(), "Debug mode not accessible after second launch"

    # Cleanup
    kill_all_chrome_processes()
    await asyncio.sleep(5)



def test_config_loading():
    """Test configuration overrides using environment variables"""
    
    # 1. Verify Default Configuration
    # We clear relevant env vars first to be safe (though test runner isolation usually handles this)
    if 'CHROME_PROFILE_DIRECTORY' in os.environ: del os.environ['CHROME_PROFILE_DIRECTORY']
    if 'CHROME_DOWNLOAD_DIRECTORY' in os.environ: del os.environ['CHROME_DOWNLOAD_DIRECTORY']
    
    default_config = get_browser_config()
    # Assuming "Profile 1" is the hardcoded default in browser_launcher.py
    assert default_config['browser']['chrome_profile_directory'] == "Profile 1"

    # 2. Test Override chrome_profile_directory using environment variable
    os.environ['CHROME_PROFILE_DIRECTORY'] = "Override Profile"
    config = get_browser_config()
    assert config['browser']['chrome_profile_directory'] == "Override Profile"

    # 3. Test Override download_directory using environment variable
    os.environ['CHROME_DOWNLOAD_DIRECTORY'] = "/override/downloads"
    config = get_browser_config()
    assert config['browser']['download_directory'] == "/override/downloads"

    # Cleanup environment variables
    if 'CHROME_PROFILE_DIRECTORY' in os.environ: del os.environ['CHROME_PROFILE_DIRECTORY']
    if 'CHROME_DOWNLOAD_DIRECTORY' in os.environ: del os.environ['CHROME_DOWNLOAD_DIRECTORY']


@pytest.mark.asyncio
async def test_browser_startup_timeout():
    """Test browser startup with actual timeout"""
    # First, kill all Chrome processes to ensure a clean state
    kill_all_chrome_processes()
    await asyncio.sleep(2)

    # Temporarily set remote_debugging_port to an unused port to simulate timeout
    unused_port = 9999
    try:
        os.environ['CHROME_REMOTE_DEBUGGING_PORT'] = str(unused_port)
        
        # Mock subprocess.Popen to do nothing, preventing the browser from starting
        with patch('subprocess.Popen'):
            with pytest.raises(TimeoutError):
                # launch_browser will call Popen (which does nothing now)
                # and then wait_for_browser_start will wait for the port to open
                # which will never happen, causing TimeoutError.
                await launch_browser()
    finally:
        # Clean up environment variable to not affect other tests
        if 'CHROME_REMOTE_DEBUGGING_PORT' in os.environ:
            del os.environ['CHROME_REMOTE_DEBUGGING_PORT']
        kill_all_chrome_processes()
        await asyncio.sleep(2)


def test_kill_nonexistent_browser():
    """Test killing Chrome when no processes exist"""
    # Ensure no Chrome is running
    kill_all_chrome_processes()
    assert not get_chrome_pids(), "Chrome processes found before test"

    # Attempt to kill Chrome processes when none exist
    try:
        kill_all_chrome_processes()
    except Exception as e:
        pytest.fail(f"kill_all_chrome_processes raised an exception when no processes exist: {e}")


@pytest.mark.asyncio
async def test_debug_mode_check():
    """Test debug mode detection with actual browser"""
    # Initial state
    assert not await is_browser_opened_in_debug_mode(), "Debug mode active before browser launch"

    # Launch browser
    await launch_browser()

    # Allow some time for Chrome to start and listen on the debug port
    await asyncio.sleep(5)

    # Verify debug mode
    port = get_browser_config()["browser"]["remote_debugging_port"]
    assert await is_browser_opened_in_debug_mode(), "Debug mode not detected after launch"
    assert is_port_in_use(port), "Debug port not actually listening after launch"

    # Kill browser
    kill_all_chrome_processes()

    # Allow processes time to fully terminate
    await asyncio.sleep(5)

    # Verify debug mode inactive
    assert not await is_browser_opened_in_debug_mode(), "Debug mode still active after kill"
    assert not is_port_in_use(port), "Debug port still in use after kill"
