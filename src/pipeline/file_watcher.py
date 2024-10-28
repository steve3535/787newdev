# src/pipeline/file_watcher.py

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
import logging
import shutil
import time
from typing import Optional
import sys
from datetime import datetime

# Adjust imports for src directory structure
from ..validators.file_validator import FileValidator
from ..processors.data_processor import DataProcessor

# Setup logging at module level
def setup_logging():
    src_dir = Path(__file__).parent.parent
    log_file = src_dir / 'lottery_pipeline.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_file)),
            logging.StreamHandler()  # This will print to console too
        ]
    )
    logging.info("File watcher starting up...")

class LotteryFileHandler(FileSystemEventHandler):
    def __init__(self):
        # Get src directory path (parent of pipeline directory)
        src_dir = Path(__file__).parent.parent
        
        # Define directories relative to src
        self.input_dir = src_dir / 'input'
        self.processed_dir = src_dir / 'processed'
        self.failed_dir = src_dir / 'failed'
        
        # Initialize components
        self.validator = FileValidator()
        self.processor = DataProcessor()
        
        # Ensure all directories exist
        self.input_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)
        
        logging.info(f"Watching directory: {self.input_dir}")

    def _move_file(self, file_path: Path, destination_dir: Path) -> None:
        """Move file to appropriate directory with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{file_path.name}"
        shutil.move(str(file_path), str(destination_dir / new_filename))
        logging.info(f"Moved {file_path.name} to {destination_dir.name}/{new_filename}")
        
    def process_file(self, file_path: Path) -> bool:
        """Process a single file through validation and processing pipeline."""
        logging.info(f"============= Starting Process =============")
        logging.info(f"Processing new file: {file_path.name}")
        
        try:
            # Step 1: Validate file
            logging.info("Step 1: Starting file validation...")
            validation_result = self.validator.validate_file(str(file_path))
            
            if not validation_result.is_valid:
                logging.error("Validation Failed!")
                for error in validation_result.errors:
                    logging.error(f"{error.error_type}: {error.message}")
                    if error.details:
                        logging.error(f"Details: {error.details}")
                self._move_file(file_path, self.failed_dir)
                return False
            
            logging.info("Validation Successful!")
            logging.info(f"Found {len(validation_result.data)} records in file")
                
            # Step 2: Process validated file
            try:
                logging.info("Step 2: Starting data processing...")
                result_df = self.processor.process_daily_file(str(file_path))
                
                # Save consolidated output
                output_file = self.processed_dir / f"consolidated_{file_path.stem}.csv"
                result_df.to_csv(output_file, index=False)
                logging.info(f"Successfully processed {len(result_df)} records")
                logging.info(f"Saved consolidated output to {output_file}")
                
                self._move_file(file_path, self.processed_dir)
                logging.info("File processing completed successfully")
                return True
                
            except ValueError as e:
                if "already processed" in str(e):
                    logging.warning(f"File already processed: {file_path.name}")
                    self._move_file(file_path, self.failed_dir)
                    return False
                raise
                
        except Exception as e:
            logging.error(f"Error processing {file_path.name}: {str(e)}")
            logging.error("Exception details:", exc_info=True)  # This will print stack trace
            self._move_file(file_path, self.failed_dir)
            return False
        finally:
            logging.info(f"============= Process Complete =============\n")

    def on_created(self, event):
        """Handle new file creation event."""
        if event.is_directory:
            return
            
        file_path = Path(event.src_path)
        if file_path.suffix.lower() == '.csv':
            self.process_file(file_path)

def start_watcher():
    """Start the file watching pipeline."""
    setup_logging()  # Initialize logging first
    
    src_dir = Path(__file__).parent.parent
    input_dir = src_dir / 'input'
    
    logging.info(f"Starting file watcher on directory: {input_dir}")
    
    event_handler = LotteryFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(input_dir), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Stopping file watcher...")
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watcher()