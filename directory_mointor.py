import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileAddHandler(FileSystemEventHandler):
    """
    Custom event handler for file monitoring.
    Triggers the decryption callback when a new file is created.
    """

    def __init__(self, decryption_callback):
        """
        Initialize the handler with a decryption callback function.

        Args:
            decryption_callback (function): Function to call when a new file is detected.
        """
        self.decryption_callback = decryption_callback

    def on_created(self, event):
        """
        Called when a new file is created in the monitored directory.

        Args:
            event (FileSystemEvent): The event object containing details about the file.
        """
        if not event.is_directory:
            print(f"[+] New file detected: {event.src_path}")
            # Wait for the file to be fully written before triggering the callback
            self.wait_for_file_completion(event.src_path)
            self.decryption_callback(event.src_path)

    def wait_for_file_completion(self, file_path, timeout=10, check_interval=0.5):
        """
        Wait until the file size stops changing to ensure the file is fully written.

        Args:
            file_path (str): Path to the file being monitored.
            timeout (int): Maximum time to wait for the file to complete (in seconds).
            check_interval (float): Time interval between file size checks (in seconds).
        """
        start_time = time.time()
        previous_size = -1

        while time.time() - start_time < timeout:
            try:
                current_size = os.path.getsize(file_path)
                if current_size == previous_size:
                    # File size has stopped changing
                    print(f"[+] File is fully written: {file_path}")
                    return
                previous_size = current_size
            except FileNotFoundError:
                # File might not exist yet
                pass
            time.sleep(check_interval)

        print(f"[!] Timeout reached for file: {file_path}")


class DirectoryMonitor:
    """
    Monitors a directory for new files and triggers a decryption callback when a file is created.
    """

    def __init__(self, directory, decryption_callback):
        """
        Initialize the directory monitor.

        Args:
            directory (str): Path to the directory to monitor.
            decryption_callback (function): Function to call when a new file is detected.
        """
        self.directory = directory
        self.decryption_callback = decryption_callback
        self.observer = None
        self.monitor_thread = None
        self.running = False

    def start(self):
        """
        Start monitoring the directory.
        """
        if self.running:
            print("[!] Monitoring is already running.")
            return

        print(f"[*] Starting to monitor directory: {self.directory}")
        self.running = True

        # Create the directory if it doesn't exist
        os.makedirs(self.directory, exist_ok=True)

        # Initialize the observer and event handler
        self.observer = Observer()
        event_handler = FileAddHandler(self.decryption_callback)
        self.observer.schedule(event_handler, self.directory, recursive=False)
        self.observer.start()

        # Start the observer in a separate thread
        self.monitor_thread = threading.Thread(target=self._run_observer, daemon=True)
        self.monitor_thread.start()
        print("[*] Monitoring started.")

    def _run_observer(self):
        """
        Internal method to keep the observer running.
        """
        while self.running:
            time.sleep(1)

    def stop(self):
        """
        Stop monitoring the directory.
        """
        if not self.running:
            print("[!] Monitoring is not running.")
            return

        print("[!] Stopping directory monitoring...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        print("[*] Monitoring stopped.")