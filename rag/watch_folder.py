import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from rag.config import UPDATED_DIR
from rag.ingest import ingest_documents, setup_directories

class PDFHandler(FileSystemEventHandler):
    def on_created(self, event):
        # We only care about new PDF files
        if not event.is_directory and event.src_path.lower().endswith('.pdf'):
            print(f"New PDF detected: {event.src_path}")
            # Wait a moment to ensure the file is completely written by the OS before processing
            time.sleep(2)
            try:
                ingest_documents()
            except Exception as e:
                print(f"Error during ingestion: {e}", file=sys.stderr)

def start_watching():
    setup_directories()
    
    event_handler = PDFHandler()
    observer = Observer()
    observer.schedule(event_handler, UPDATED_DIR, recursive=False)
    
    print(f"Watching for new PDF files in {UPDATED_DIR}...")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped watching.")
        
    observer.join()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    start_watching()
