import os
import logging
import datetime as dt

# 全局变量
# 定位到本文件所在目录
__BASE_DIR__ = os.path.dirname(os.path.abspath(__file__))

"""初始化文件夹结构"""
# 检查__BASE_DIR__中是否存在明为mission的文件夹，如果不存在，创建一个
if not os.path.exists(os.path.join(__BASE_DIR__, "mission")):
    os.makedirs(os.path.join(__BASE_DIR__, "mission"))
# 检查__BASE_DIR__中是否存在明为screenshot_target的文件夹，如果不存在，创建一个
if not os.path.exists(os.path.join(__BASE_DIR__, "screenshot_target")):
    os.makedirs(os.path.join(__BASE_DIR__, "screenshot_target"))
# 检查__BASE_DIR__中是否存在明为log的文件夹，如果不存在，创建一个
if not os.path.exists(os.path.join(__BASE_DIR__, "log")):
    os.makedirs(os.path.join(__BASE_DIR__, "log"))

# 日志配置
# 创建日志记录器
logger = logging.getLogger("doAuto")
logger.setLevel(logging.DEBUG)
# 创建日志处理器
file_handler = logging.FileHandler(
    f"{__BASE_DIR__}\\log\\app_{dt.datetime.now().strftime('%Y_%m_%d')}.log"
)
file_handler.setLevel(logging.DEBUG)
# 创建日志格式化器
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# 将日志格式化器添加到日志处理器中
file_handler.setFormatter(formatter)
# 将日志处理器添加到日志记录器中
logger.addHandler(file_handler)
