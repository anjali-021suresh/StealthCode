import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

# Custom event handler for file monitoring
class FileAddHandler(FileSystemEventHandler):
    def __init__(self, decryption_callback):
        self.decryption_callback = decryption_callback # pass the function without ()

    def on_created(self, event):
        if not event.is_directory:
            print(f"[+] New file detected: {event.src_path}")
            # Call the decryption function for the new file
            self.decryption_callback(event.src_path)


# Class to manage directory monitoring
class DirectoryMonitor:
    def __init__(self, directory, decryption_callback):
        self.directory = directory
        self.decryption_callback = decryption_callback
        self.observer = None
        self.monitor_thread = None
        self.running = False

    def start(self):
        if self.running:
            print("[!] Monitoring is already running.")
            return

        print(f"[*] Starting to monitor directory: {self.directory}")
        self.running = True
        self.observer = Observer()
        event_handler = FileAddHandler(self.decryption_callback)
        self.observer.schedule(event_handler, self.directory, recursive=False)
        self.observer.start()

        # Run observer in a separate thread
        self.monitor_thread = threading.Thread(target=self._run_observer, daemon=True)
        self.monitor_thread.start()
        print("[*] Monitoring started.")

    def _run_observer(self):
        while self.running:
            time.sleep(1)

    def stop(self):
        if not self.running:
            print("[!] Monitoring is not running.")
            return

        print("[!] Stopping directory monitoring...")
        self.running = False
        self.observer.stop()
        self.observer.join()
        print("[*] Monitoring stopped.")



