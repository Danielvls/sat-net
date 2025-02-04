import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
import psutil

class Logger:
    _instance = None

    def __new__(cls):
        '''this is a singleton class'''
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self):
        '''setup logger'''
        self.PROJECTROOT = Path(__file__).parent.parent.parent

        # 创建logs目录，如果不存在
        logs_dir = self.PROJECTROOT / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        # 获取当前时间，并格式化为文件名的一部分
        current_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_filename = logs_dir / f"debug_{current_time}.log"

        # 创建logger对象
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # 调试日志文件处理器（仅DEBUG级别）
        debug_handler = logging.handlers.RotatingFileHandler(
            log_filename,
            maxBytes=1024*1024,  # 1MB
            backupCount=3,
            encoding="utf-8",
            mode='w'  # 每次运行时都会新建文件
        )
        debug_handler.setLevel(logging.DEBUG)

        # 创建控制台Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别的日志
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        debug_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 将Handler添加到logger
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(console_handler)

    def log_system_usage(self):
        """Log system resources usage including CPU and Memory."""
        try:
            # 获取 CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.logger.info(f"CPU Usage: {cpu_percent}%")

            # 获取内存使用情况
            memory_info = psutil.virtual_memory()
            memory_percent = memory_info.percent
            self.logger.debug(f"Memory Usage: {memory_percent}%")

            # 获取可用内存
            available_memory = memory_info.available / (1024 ** 2)  # MB
            self.logger.debug(f"Available Memory: {available_memory} MB")

        except Exception as e:
            self.logger.error(f"Error in logging system resources usage: {e}")

    def get_logger(self):
        return self.logger
