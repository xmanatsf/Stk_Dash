import logging
import os

def setup_logging():
    """
    Sets up basic logging for the application.
    Logs to console and a file.
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Log to console
            logging.FileHandler(log_file) # Log to file
        ]
    )
    logging.getLogger('urllib3').setLevel(logging.WARNING) # Suppress urllib3 warnings
    logging.getLogger('requests').setLevel(logging.WARNING) # Suppress requests warnings
    logging.info("Logging setup complete.")

if __name__ == "__main__":
    setup_logging()
    logging.info("Test message from setup_logger.py")