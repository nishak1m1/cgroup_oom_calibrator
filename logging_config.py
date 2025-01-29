import logging

def setup_logging():
    """Configures logging for the application."""
    logging.basicConfig(
        filename='calibration_logger.log',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
