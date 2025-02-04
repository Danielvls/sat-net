import logging
import logging.handlers
from pathlib import Path

# ================= 基础配置 =================
# 创建日志目录
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 基础配置（简单用法）
logging.basicConfig(
    level=logging.DEBUG,  # 设置根记录器级别
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "basic.log"),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 获取日志记录器
logger = logging.getLogger(__name__)

# ================= 日志级别示例 =================
logger.debug("这是一条debug信息")      # 最详细的日志信息（调试用）
logger.info("这是一条info信息")        # 常规运行信息
logger.warning("这是一条warning信息")  # 警告信息（不影响运行）
logger.error("这是一条error信息")      # 严重错误（程序仍可运行）
logger.critical("这是一条critical信息") # 致命错误（程序可能无法继续运行）

# ================= 高级配置 =================
# 创建自定义日志记录器（推荐方式）
custom_logger = logging.getLogger("MyApp")
custom_logger.setLevel(logging.DEBUG)  # 设置日志记录器级别

# 创建格式化器
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 文件处理器（带日志轮转）
file_handler = logging.handlers.RotatingFileHandler(
    log_dir / "app.log",
    maxBytes=1024*1024,  # 1MB
    backupCount=5,       # 保留5个备份
    encoding="utf-8"
)
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)  # 控制台只显示INFO及以上级别

# 添加处理器到记录器
custom_logger.addHandler(file_handler)
custom_logger.addHandler(console_handler)

# 使用自定义日志记录器
custom_logger.debug("调试信息")
custom_logger.info("程序启动")
custom_logger.warning("磁盘空间不足80%")
try:
    1 / 0
except ZeroDivisionError:
    custom_logger.error("发生除零错误", exc_info=True)  # 记录异常堆栈

# ================= 日志过滤器示例 =================
class InfoFilter(logging.Filter):
    """只允许INFO级别的日志通过"""
    def filter(self, record):
        return record.levelno == logging.INFO

# 创建专用INFO处理器
info_handler = logging.FileHandler(log_dir / "info.log")
info_handler.setLevel(logging.INFO)
info_handler.addFilter(InfoFilter())
info_handler.setFormatter(formatter)
custom_logger.addHandler(info_handler)

custom_logger.info("这是一条INFO级别的特殊记录")  # 会被info.log记录
custom_logger.debug("这条debug不会被info.log记录") 

# ================= 多模块日志示例 =================
# 在子模块中使用日志（会自动继承父记录器配置）
module_logger = logging.getLogger("MyApp.SubModule")
module_logger.info("这是来自子模块的日志")

# ================= 定时日志轮转示例 =================
# 每天生成一个日志文件，保留7天
timed_handler = logging.handlers.TimedRotatingFileHandler(
    log_dir / "daily.log",
    when="midnight",  # 每天午夜
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
timed_handler.setFormatter(formatter)
custom_logger.addHandler(timed_handler)

custom_logger.info("这条日志会进入每日轮转文件")

# ================= 日志关闭 =================
# 程序退出前关闭所有日志处理器
for handler in custom_logger.handlers:
    handler.close()