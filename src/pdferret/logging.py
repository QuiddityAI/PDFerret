import logging
import logging.handlers

logger = logging.getLogger()
logger.setLevel(logging.WARN)
handler = logging.handlers.RotatingFileHandler("pdferret.log", maxBytes=(1048576 * 5), backupCount=10)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())
