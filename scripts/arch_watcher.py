#!/usr/bin/env python3
"""
NeuralAgent Architecture Visualization - File Watcher
Watches the project directory for changes and notifies the frontend
"""

import os
import time
import sys
from pathlib import Path
from typing import List, Set

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent
except ImportError:
    print("Installing watchdog...")
    os.system(f"{sys.executable} -m pip install watchdog")
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.changes: Set[str] = set()
        self.last_update = time.time()
        
    def on_modified(self, event):
        if event.is_directory:
            return
        if '__pycache__' in event.src_path or '.git' in event.src_path:
            return
        self._add_change(event.src_path)
        
    def on_created(self, event):
        if event.is_directory:
            return
        if '__pycache__' in event.src_path or '.git' in event.src_path:
            return
        self._add_change(event.src_path)
    
    def _add_change(self, path: str):
        try:
            rel_path = Path(path).relative_to(Path(__file__).parent.parent)
            self.changes.add(str(rel_path))
        except ValueError:
            pass
        
    def get_changes(self) -> List[str]:
        changes = list(self.changes)
        self.changes.clear()
        return changes

def main():
    print("=" * 80)
    print("  NeuralAgent Architecture Visualization - File Watcher")
    print("=" * 80)
    
    root_dir = Path(__file__).parent.parent
    print(f"\nWatching directory: {root_dir}")
    
    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, str(root_dir), recursive=True)
    
    print("File watcher started! Changes will be detected...")
    print("\n" + "=" * 80)
    print("  Starting frontend dev server...")
    print("=" * 80)
    print("\nThe visualization website should open automatically!")
    print("If not, visit: http://localhost:5173")
    print("=" * 80)
    
    observer.start()
    
    try:
        while True:
            changes = event_handler.get_changes()
            if changes:
                print(f"\n[{time.strftime('%H:%M:%S')}] Detected changes:")
                for change in changes:
                    print(f"  • {change}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        observer.stop()
        observer.join()
        print("Watcher stopped.")

if __name__ == "__main__":
    main()
