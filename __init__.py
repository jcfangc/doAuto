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

# 在mission文件夹中，生成md格式软件说明
with open(os.path.join(__BASE_DIR__, "mission", "README.md"), "w") as f:
    f.write(
        """
## **软件功能**

* 本软件是一个自动化软件，可以实现录制好的自动化的任务，包括：
    * 鼠标：单击、双击、右击、拖拽、滚轮滚动
    * 键盘：除了 “CTRL + SHIFT + K” 以外的键盘输入，该热键被用于结束键盘记录

## **软件使用**

* 脚本执行：
    * 点击相应的脚本名称后点击 “执行任务” 即可执行相应任务脚本

* 脚本录制：
    * 如果程序菜单中没有想要执行的任务脚本，请点击 “录制任务” 
    * 过程中可以使用 “方向键” 控制截图框大小
    * 使用 “SHIFT + K” 录制键盘输入
    * 使用 “CTRL + SHIFT + K” 结束键盘输入
    * 使用 “Esc” 键结束任务录制，并命名任务脚本

* 脚本编辑：
    * 点击相应的脚本名称后点击 “编辑任务” 即可编辑相应任务脚本
    * 在脚本的 “后续” 一栏中，可以加入指定的修饰，丰富脚本行为，目前支持的修饰有：
        * LOOP(q)：循环执行脚本本行至 q 行内容，无限循环，直至程序无法继续执行并退出
        * LOOP(q,t)：循环执行脚本本行至 q 行内容，重复 t 次
    * 由于本软件的截图方式的限制，当按钮样式在鼠标悬浮时发生变化时，所截取的目标图片可能与实际不符，此时请重新手动截图，替换原有的目标图片
        * 请在 “screenshot_target” 文件夹中替换相应的目标图片
        * 请将 “mission” 文件夹中对应脚本中的 “截图” 相关路径也进行相应替换

* 脚本删除：
    * 点击相应的脚本名称后点击 “删除任务” 即可删除相应任务脚本


## **联系方式**

* 对软件有任何建议或者意见，欢迎联系我，一起交流学习，谢谢！
    * github: jcfangc

"""
    )
