import logging
from devtools import PrettyFormat
from src.config import config


def init_logging():
    logging_level = logging.ERROR
    match config.logging_level:
        case "INFO":
            logging_level = logging.INFO
        case "DEBUG":
            logging_level = logging.DEBUG
        case "ERROR":
            logging_level = logging.ERROR
        case "WARNING":
            logging_level = logging.WARNING
        case "CRITICAL":
            logging_level = logging.CRITICAL
        case "FATAL":
            logging_level = logging.FATAL
    logger = logging.getLogger("ServiceCheatingGraphics")
    logger.setLevel(logging_level)
    # logger = logging.getLogger('uvicorn.error')
    # logger.setLevel(logging_level)
    logging.basicConfig(level=logging_level)

    pformat = PrettyFormat()
    config_formatted = pformat(config)

    logger = logging.getLogger("ServiceCheating")
    logger.info(f"Effective config:\n{config_formatted}")