import logging
import os
from datetime import datetime
from app_paths import user_data_path

# Ensure logs directory exists
log_directory = user_data_path("logs")
os.makedirs(log_directory, exist_ok=True)

# Generate log file name with current date
current_date = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(log_directory, f"script_{current_date}.log")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",  # Custom format
    datefmt="%H:%M",  # Display only hours and minutes
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),  # Log to a date-specific file
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger(__name__)

# if __name__ == "__main__":
#     logger.debug("Debug message: for detailed internal states.")
#     logger.info("Info message: for general script status.")
#     logger.warning("Warning message: something might be wrong.")
#     logger.error("Error message: something went wrong.")
