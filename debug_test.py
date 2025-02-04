import logging
import logging.handlers
from pathlib import Path

# ================= 日志配置 =================
def setup_logger():
    """配置日志记录器"""
    log_dir = Path("debug_logs")
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("DataProcessor")
    logger.setLevel(logging.DEBUG)  # 启用DEBUG级别

    # 调试日志文件处理器（仅DEBUG级别）
    debug_handler = logging.handlers.RotatingFileHandler(
        log_dir / "debug.log",
        maxBytes=1024*1024,  # 1MB
        backupCount=3,
        encoding="utf-8"
    )
    debug_handler.setLevel(logging.DEBUG)

    # 控制台处理器（INFO级别以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 统一日志格式
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    debug_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(debug_handler)
    logger.addHandler(console_handler)
    return logger

# 初始化日志记录器
logger = setup_logger()

# ================= 数据处理函数 =================
def process_data(data):
    """
    数据处理函数（模拟真实业务逻辑）
    功能：将字符串数据转换为整数并计算平均值
    """
    logger.debug("进入 process_data 函数")
    logger.debug(f"原始数据: {data} (类型: {type(data)})")
    
    try:
        # 数据清洗
        logger.debug("开始数据清洗")
        cleaned_data = [x.strip() for x in data.split(",")]
        logger.debug(f"清洗后数据: {cleaned_data}")
        
        # 类型转换
        logger.debug("开始类型转换")
        numbers = []
        for index, item in enumerate(cleaned_data):
            try:
                num = int(item)
                numbers.append(num)
                logger.debug(f"成功转换第 {index+1} 项: {item} -> {num}")
            except ValueError:
                logger.warning(f"无法转换第 {index+1} 项: {item}")
                continue
                
        logger.debug(f"转换后数字列表: {numbers}")
        
        # 计算平均值
        logger.debug("开始计算平均值")
        average = sum(numbers) / len(numbers)
        logger.debug(f"计算结果: {sum(numbers)} / {len(numbers)} = {average}")
        
        return average
    
    except Exception as e:
        logger.error("数据处理过程中发生错误", exc_info=True)
        raise

# ================= 测试用例 =================
if __name__ == "__main__":
    # 正常测试数据
    test_data1 = " 23, 45, 78, 91, 102 "  # 故意包含空格
    logger.info(f"测试数据1: {test_data1}")
    try:
        result = process_data(test_data1)
        logger.info(f"测试1结果: {result:.2f}")
    except:
        pass
    
    # 问题测试数据（包含无法转换的字符串）
    test_data2 = "56, 72, hello, 88, 104"  # 包含非法字符
    logger.info(f"\n测试数据2: {test_data2}")
    try:
        result = process_data(test_data2)
    except:
        logger.info("测试2发生预期中的错误")

# ================= 日志分析指引 =================
"""
生成的 debug.log 文件会包含：
1. 完整的函数调用流程
2. 关键变量的中间状态
3. 每个数据处理步骤的详细信息
4. 错误发生的上下文环境

当遇到问题时，可以查看debug日志：
1. 定位错误发生的位置
2. 查看错误发生前的变量状态
3. 跟踪数据处理流程
4. 分析类型转换失败的具体原因
"""