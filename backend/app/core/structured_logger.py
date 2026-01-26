import logging
import sys
import uuid
from typing import Any

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
    def info(self, msg: str, **kwargs):
        self._log(logging.INFO, msg, **kwargs)
        
    def warning(self, msg: str, **kwargs):
        self._log(logging.WARNING, msg, **kwargs)
        
    def error(self, msg: str, **kwargs):
        self._log(logging.ERROR, msg, **kwargs)
        
    def exception(self, msg: str, **kwargs):
        self.logger.exception(msg, extra=kwargs)

    def _log(self, level, msg, **kwargs):
        if kwargs:
            extra_str = " ".join([f"{k}={v}" for k, v in kwargs.items()])
            msg = f"{msg} | {extra_str}"
        self.logger.log(level, msg)

def get_logger(name: str):
    return StructuredLogger(name)
