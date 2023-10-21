import sys
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import keyboard
import datetime as dt
import pyautogui as pag
import os
import shutil
import inspect

from PyQt5.QtCore import pyqtSignal
from pynput import mouse
from PIL import ImageGrab
from pandas import DataFrame
from init_config import __BASE_DIR__, logger


class MouseListener(QtCore.QThread):
    """鼠标监听器"""

    # 鼠标信号
    mousePressed = pyqtSignal(int, int, mouse.Button, bool)
    mouseScroll = pyqtSignal(int, int, int, int)

    # 初始化
    def run(self):
        with mouse.Listener(
            on_click=self.on_click, on_scroll=self.on_scroll
        ) as listener:
            listener.join()

    def on_click(self, x, y, button, pressed):
        self.mousePressed.emit(x, y, button, pressed)

    def on_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件"""
        self.mouseScroll.emit(x, y, dx, dy)


class MissionCreate(QtWidgets.QWidget):
    """任务创建器"""

    # 键盘信号
    up_singal = pyqtSignal()
    down_singal = pyqtSignal()
    left_singal = pyqtSignal()
    right_singal = pyqtSignal()
    esc_singal = pyqtSignal()
    start_record_signal = pyqtSignal()
    stop_recording_signal = pyqtSignal()

    # 鼠标信号
    left_button_double_click_signal = pyqtSignal(str)
    left_button_single_click_signal = pyqtSignal(str)
    right_button_single_click_signal = pyqtSignal(str)
    long_press_signal = pyqtSignal(str)
    button_release_signal = pyqtSignal(str)
    mouse_roll_signal = pyqtSignal(str)

    # 其他信号
    screenshot_area_signal = pyqtSignal(QtCore.QPoint)
    have_dialog_signal = pyqtSignal()

    import missionAuto as ma

    def __init__(self, auto_caller: ma.MissionAuto):
        super().__init__()

        self.auto_caller = auto_caller
        self.logger = logger
        # log新的运行开始了
        self.print_and_log(
            """\n
            *********************************\n
            * MissionCreator：新的运行开始了！*\n
            *********************************
            """
        )

        self.last_press_time = dt.datetime.now()
        self.edge_width = 3
        self.white_frame_style = f"background-color: rgba(0,0,0,0); border: {self.edge_width}px solid rgba(255,255,255,128);"
        self.black_frame_style = f"background-color: rgba(0,0,0,0); border: {self.edge_width}px solid rgba(0,0,0,128);"
        self.screenshot_area_width = 80
        self.screenshot_area_height = 80
        self.white_frame_width = self.screenshot_area_width + self.edge_width * 2
        self.white_frame_height = self.screenshot_area_height + self.edge_width * 2
        self.black_frame_width = self.white_frame_width + self.edge_width * 2
        self.black_frame_height = self.white_frame_height + self.edge_width * 2
        self.closing = False
        self.make_mistake = True
        self.key_rec = False
        self.state = []
        self.ok = ""

        # 链接信号和槽函数
        # 键盘信号
        self.up_singal.connect(self.increase_height)
        self.down_singal.connect(self.decrease_height)
        self.left_singal.connect(self.decrease_width)
        self.right_singal.connect(self.increase_width)
        self.esc_singal.connect(self.close)
        self.start_record_signal.connect(self.start_recording)
        self.stop_recording_signal.connect(self.stop_recording)

        # 鼠标信号
        self.left_button_double_click_signal.connect(self.push_record)
        self.left_button_single_click_signal.connect(self.push_record)
        self.right_button_single_click_signal.connect(self.push_record)
        self.long_press_signal.connect(self.push_record)
        self.button_release_signal.connect(self.push_record)
        self.mouse_roll_signal.connect(self.push_record)

        # 其他信号
        self.screenshot_area_signal.connect(self.detect_screenshot_area_cover)
        self.have_dialog_signal.connect(self.have_dialog)

        # 初始化交互界面
        self.init_ui()

        self.showFullScreen()
        self.update_position()
        self.keyboard_manage()
        self.mouse_manage()

    # 初始化交互界面
    def init_ui(self):
        # 设置窗口为全屏，无边框，背景透明，无法获取焦点（不会接收鼠标点击）
        self.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowTransparentForInput)
            # | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
            | QtCore.Qt.WindowType.Window
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.move(0, 0)
        self.resize(pag.size()[0], pag.size()[1])

        # 创建一个标签
        self.prompt_label = QtWidgets.QLabel(self)
        font = QtGui.QFont()
        font.setFamilies(["Microsoft YaHei UI"])
        self.prompt_label.setFont(font)
        self.prompt_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.setStyleSheet(
            f"font-size:{self.height()//50}px;color: white;background-color: rgba(0,0,0,128);"
        )
        self.prompt_label.hide()

        # 创建一个消息栏
        self.info_bar = QtWidgets.QWidget(self)
        # 设置大小
        self.info_bar.resize(self.width() // 4, self.height())
        # 设置记录表为frameless窗口
        self.info_bar.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowType.CustomizeWindowHint
            | QtCore.Qt.WindowType.FramelessWindowHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.WindowTransparentForInput
        )
        # 设置的背景色，字体颜色，边框颜色
        self.info_bar.setStyleSheet(
            "background-color: rgba(0,0,0,128); color: white; border: 1px solid rgba(0,0,0,128);"
        )

        # 创建一个操作提示标签
        self.operate_table = QtWidgets.QTableWidget(self.info_bar)
        # 设置记录表为frameless窗口
        self.operate_table.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        )
        self.operation_column = ["输入和意义"]
        self.operate_table.setColumnCount(len(self.operation_column))
        self.operate_table.setHorizontalHeaderLabels(self.operation_column)
        self.operate_table.resize(self.info_bar.width(), self.info_bar.height() // 4)
        for i in range(self.operate_table.columnCount()):
            self.operate_table.setColumnWidth(
                i, self.info_bar.width() // self.operate_table.columnCount()
            )
        # 设置字体
        font = QtGui.QFont()
        font.setFamilies(["Microsoft YaHei UI"])
        self.operate_table.setFont(font)
        # 不允许被键盘控制
        self.operate_table.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # 输入默认值
        motion_list = [
            "'↑ 上方向键'------拉高截图区域",
            "'↓ 下方向键'------降低截图区域",
            "'← 左方向键'------缩短截图区域",
            "'→ 右方向键'------拉长截图区域",
            "'Esc 退出键'------结束截图",
            "鼠标点击------截图",
            "'Shift + K'------录制键盘活动",
            "'Shift + Ctrl + K'------停止录制键盘活动",
        ]
        for value in motion_list:
            row = self.operate_table.rowCount()
            self.operate_table.insertRow(row)
            self.operate_table.setItem(
                row,
                self.operation_column.index("输入和意义"),
                QtWidgets.QTableWidgetItem(value),
            )
            # 设置单元格的对齐方式
            self.operate_table.item(
                row, self.operation_column.index("输入和意义")
            ).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # 设置表头的背景色，字体颜色
        self.operate_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: rgba(0,0,0,128); color: white; }"
        )
        # 设置的背景色，字体颜色，边框颜色
        self.operate_table.setStyleSheet(
            "background-color: rgba(0,0,0,128); color: white; border: 1px solid rgba(0,0,0,128);"
        )
        # 设置不显示行号
        self.operate_table.verticalHeader().setVisible(False)

        # 创建一个操作记录表
        self.record_table = QtWidgets.QTableWidget(self.info_bar)
        # 设置记录表为frameless窗口
        self.record_table.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        )
        self.record_column = ["操作", "截图", "状态", "后续"]
        # 创建一个dataframe，用于存储操作记录
        self.mission_dataframe = DataFrame(columns=self.record_column)
        self.record_table.setColumnCount(len(self.record_column) - 1)  # 不显示后续
        self.record_table.setHorizontalHeaderLabels(self.record_column[0:3])  # 不显示后续
        self.record_table.resize(self.info_bar.width(), self.info_bar.height() * 3 // 4)
        # 设置表头的宽度
        # 操作
        self.record_table.setColumnWidth(
            0, self.record_table.width() // self.record_table.columnCount() // 2
        )
        # 截图
        self.record_table.setColumnWidth(
            1, self.record_table.width() // self.record_table.columnCount() // 2
        )
        # 状态
        self.record_table.setColumnWidth(
            2,
            self.record_table.width() // self.record_table.columnCount() * 2,
        )
        # 设置每行高度
        self.record_table.verticalHeader().setDefaultSectionSize(
            self.record_table.width() // self.record_table.columnCount() // 2
        )
        # 设置表头的背景色，字体颜色
        self.record_table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { background-color: rgba(0,0,0,128); color: white; }"
        )
        # 设置的背景色，字体颜色，边框颜色
        self.record_table.setStyleSheet(
            "background-color: rgba(0,0,0,128); color: white; border: 1px solid rgba(0,0,0,128);"
        )
        # 设置行号颜色
        self.record_table.verticalHeader().setStyleSheet(
            "QHeaderView::section { background-color: rgba(0,0,0,128); color: white; }"
        )

        # 纳入布局
        self.info_bar_layout = QtWidgets.QVBoxLayout(self.info_bar)
        # 布局比例
        self.info_bar_layout.addWidget(self.operate_table, stretch=4)
        self.info_bar_layout.addWidget(self.record_table, stretch=6)
        # info_bar布局
        self.info_bar.setLayout(self.info_bar_layout)
        # 对齐方式
        self.info_bar_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        # 组件之间的间距
        self.info_bar_layout.setSpacing(0)
        # 边距
        self.info_bar_layout.setContentsMargins(0, 0, 0, 0)

        # 创建一个白色边框
        self.white_frame = QtWidgets.QWidget(self)
        self.white_frame.setStyleSheet(self.white_frame_style)
        self.white_frame.resize(self.white_frame_width, self.white_frame_height)

        # 创建一个黑色边框
        self.black_frame = QtWidgets.QWidget(self)
        self.black_frame.setStyleSheet(self.black_frame_style)
        self.black_frame.resize(self.black_frame_width, self.black_frame_height)

    def print_and_log(self, text: str):
        """打印并记录日志"""
        print(text)
        caller_frame = inspect.stack()[1]
        caller_line = caller_frame.lineno
        self.logger.debug(f"{text} (Called at line {caller_line})")

    # 事件绑定
    def mouse_manage(self):
        """鼠标管理"""
        self.print_and_log("正在监听鼠标...")
        # 创建鼠标监听器
        self.mouse_listener = MouseListener()
        self.mouse_listener.mousePressed.connect(self.on_click)
        self.mouse_listener.mouseScroll.connect(self.on_scroll)
        # 启动鼠标监听器
        self.mouse_listener.start()

    def on_click(self, x, y, button, pressed):
        """鼠标点击事件"""
        # operate_table中的"鼠标点击"行被选中并高亮
        self.operate_table.selectRow(5)
        # operate_table中的"鼠标点击"行，"意义"列被选中并高亮
        if not self.closing:
            if pressed:
                # 获取当前时间
                press_now = dt.datetime.now()
                # 如果两次点击的时间间隔小于0.5秒，则认为是双击
                if (
                    button == mouse.Button.left
                    and (press_now - self.last_press_time).total_seconds() < 0.5
                ):
                    self.action = "左键双击"
                    self.state = [x, y]
                    self.print_and_log(f"左键双击：{x, y}")
                    # 更新上一次点击的时间
                    self.last_press_time = press_now
                    self.left_button_double_click_signal.emit(None)
                elif button == mouse.Button.left:
                    self.action = "左键单击"
                    self.state = [x, y]
                    self.print_and_log(f"左键单击：{x, y}")
                    # 更新上一次点击的时间
                    self.last_press_time = press_now
                    self.left_button_single_click_signal.emit(self.img_capture())
                elif button == mouse.Button.right:
                    self.action = "右键单击"
                    self.state = [x, y]
                    self.print_and_log(f"右键单击：{x, y}")
                    # 更新上一次点击的时间
                    self.last_press_time = press_now
                    self.right_button_single_click_signal.emit(None)

            else:
                # 获取当前时间
                release_now = dt.datetime.now()
                duration = (release_now - self.last_press_time).total_seconds()
                if duration >= 1:
                    if button == mouse.Button.left:
                        self.action = "左键长按"
                        self.print_and_log(f"左键长按：{x, y, duration}")
                    elif button == mouse.Button.right:
                        self.action = "右键长按"
                        self.print_and_log(f"右键长按：{x, y, duration}")
                    self.state = [x, y, duration]
                    self.long_press_signal.emit(None)
                else:
                    if button == mouse.Button.left:
                        self.action = "左键释放"
                        self.print_and_log(f"左键释放：{x, y}")
                    elif button == mouse.Button.right:
                        self.action = "右键释放"
                        self.print_and_log(f"右键释放：{x, y}")
                    self.state = [x, y]
                    self.button_release_signal.emit(None)

    def on_scroll(self, x, y, dx, dy):
        """鼠标滚轮事件"""
        if not self.closing:
            self.action = "滚轮"
            self.state = [x, y, dx, dy]
            self.print_and_log(f"滚轮于{x, y}，滚动了{dx, dy}")
            self.mouse_roll_signal.emit(None)

    def detect_screenshot_area_cover(self, coords: QtCore.QPoint):
        """检测截图区域是否覆盖了记录表或弹窗"""
        # 记录表位置管理
        if (
            coords.x() + self.screenshot_area_width
            < self.width() - self.info_bar.width()
        ) and coords.x() <= 0 + self.info_bar.width():
            self.info_bar.move(self.width() - self.info_bar.width(), 0)
            self.info_bar.show()
        elif (
            coords.x() + self.screenshot_area_width
            >= self.width() - self.info_bar.width()
        ) and (coords.x() > 0 + self.info_bar.width()):
            self.info_bar.move(0, 0)
            self.info_bar.show()
        elif coords.x() <= 0 + self.info_bar.width() and (
            coords.x() + self.screenshot_area_width
            >= self.width() - self.info_bar.width()
        ):
            self.info_bar.hide()

        # 弹窗显示管理
        rec1 = self.prompt_label.geometry()
        rec2 = self.white_frame.geometry()
        if rec1.intersects(rec2):
            self.prompt_label.hide()

    def img_capture(self):
        """截图"""
        if not self.closing:
            # 获取截图
            img = ImageGrab.grab()
            # 获取色块的位置
            pos = self.screenshot_pos
            # 获取色块的坐标
            x1 = pos.x()
            y1 = pos.y()
            x2 = x1 + self.screenshot_area_width
            y2 = y1 + self.screenshot_area_height
            # 截取色块的图片
            img = img.crop((x1, y1, x2, y2))
            # 保存图片，文件名精确到毫秒
            save_path = f"{__BASE_DIR__}\\screenshot_target\\{dt.datetime.now().strftime('%Y_%m_%d-%H_%M_%S_%f')}.png"
            img.save(save_path)
            # # log截图保存时间
            # self.logger.debug(
            #     f"截图保存时间：{dt.datetime.now().strftime('%Y_%m_%d-%H_%M_%S_%f')}"
            # )
            return save_path

    def push_record(self, screenshot):
        """将记录推入表格，同时记录在dataframe中"""
        if not self.closing:
            # 获取当前行数
            row = self.record_table.rowCount()
            # 插入一行
            self.record_table.insertRow(row)

            # 将操作记录插入到表格中
            action = self.action
            self.record_table.setItem(
                row, self.record_column.index("操作"), QtWidgets.QTableWidgetItem(action)
            )
            # 设置单元格的对齐方式
            self.record_table.item(
                row, self.record_column.index("操作")
            ).setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            # 将操作记录插入到dataframe中
            self.mission_dataframe.loc[row, "操作"] = action

            # 将截图记录插入到表格中
            # 创建一个QLabel，用于显示图像
            label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(screenshot)  # 创建一个QPixmap，用于存储图像
            label.setPixmap(pixmap)
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            # 创建一个QTableWidgetItem
            item = QtWidgets.QTableWidgetItem()
            # 将QLabel插入到QTableWidgetItem中
            item.setSizeHint(label.sizeHint())
            self.record_table.setItem(row, self.record_column.index("截图"), item)
            self.record_table.setCellWidget(row, self.record_column.index("截图"), label)
            # 将截图记录插入到dataframe中
            self.mission_dataframe.loc[row, "截图"] = screenshot

            # 将状态记录插入到表格中
            state_str = str(self.state)
            self.record_table.setItem(
                row,
                self.record_column.index("状态"),
                QtWidgets.QTableWidgetItem(state_str),
            )
            # 将状态记录插入到dataframe中
            self.mission_dataframe.loc[row, "状态"] = self.state  # 不以字符串的形式存储

            # 获取最新的操作记录
            latest_record = self.mission_dataframe.iloc[-1]
            # 构建完整的日志文本
            log_text = (
                "\n最新的操作记录：\n"
                f"操作    {latest_record['操作']}\n"
                f"截图    {latest_record['截图']}\n"
                f"状态    {latest_record['状态']}"
            )
            # 输出到日志
            self.logger.debug(log_text)

            # 滑动到最后一行
            self.record_table.scrollToBottom()

    def keyboard_manage(self):
        """键盘管理"""
        self.print_and_log("正在监听键盘...")
        # 使用全局的键盘钩子来捕获键盘事件可以解决失去焦点的问题
        if not self.closing:
            keyboard.add_hotkey("up", self.up_singal.emit)
            keyboard.add_hotkey("down", self.down_singal.emit)
            keyboard.add_hotkey("left", self.left_singal.emit)
            keyboard.add_hotkey("right", self.right_singal.emit)
            keyboard.add_hotkey("esc", self.esc_singal.emit)
            keyboard.add_hotkey("shift+k", self.start_record_signal.emit)
            keyboard.add_hotkey("shift+ctrl+k", self.stop_recording_signal.emit)

    def frame_fit(self):
        self.white_frame_width = self.screenshot_area_width + self.edge_width * 2
        self.white_frame_height = self.screenshot_area_height + self.edge_width * 2
        self.black_frame_width = self.white_frame_width + self.edge_width * 2
        self.black_frame_height = self.white_frame_height + self.edge_width * 2
        self.white_frame.resize(self.white_frame_width, self.white_frame_height)
        self.black_frame.resize(self.black_frame_width, self.black_frame_height)

    def increase_height(self):
        """增加截图区域的高度"""
        if self.screenshot_area_height < self.height() and self.closing == False:
            self.screenshot_area_height += 10
            self.set_prompt(f"高度：{self.screenshot_area_height}")
            self.print_and_log(f"高度：{self.screenshot_area_height}")
            # operate_table中的"↑"上方向键行被选中并高亮
            self.operate_table.selectRow(0)
            self.frame_fit()

    def decrease_height(self):
        """减小截图区域的高度"""
        if self.screenshot_area_height > 10 and self.closing == False:
            self.screenshot_area_height -= 10
            self.set_prompt(f"高度：{self.screenshot_area_height}")
            self.print_and_log(f"高度：{self.screenshot_area_height}")
            # operate_table中的"↓"下方向键行被选中并高亮
            self.operate_table.selectRow(1)
            self.frame_fit()

    def increase_width(self):
        """增加截图区域的宽度"""
        if self.screenshot_area_width < self.width() and self.closing == False:
            self.screenshot_area_width += 10
            self.set_prompt(f"宽度：{self.screenshot_area_width}")
            self.print_and_log(f"宽度：{self.screenshot_area_width}")
            # operate_table中的"→"右方向键行被选中并高亮
            self.operate_table.selectRow(3)
            self.frame_fit()

    def decrease_width(self):
        """减小截图区域的宽度"""
        if self.screenshot_area_width > 10 and self.closing == False:
            self.screenshot_area_width -= 10
            self.set_prompt(f"宽度：{self.screenshot_area_width}")
            self.print_and_log(f"宽度：{self.screenshot_area_width}")
            # operate_table中的"←"左方向键行被选中并高亮
            self.operate_table.selectRow(2)
            self.frame_fit()

    def start_recording(self):
        self.set_prompt("开始键盘录制...")
        self.print_and_log("开始键盘录制...")
        keyboard.start_recording()

    def stop_recording(self):
        self.set_prompt("键盘录制结果")
        self.action = "键盘录制结果"
        events = keyboard.stop_recording()
        self.state = []
        for event in events:
            if event.event_type == "down":
                self.state.append(event.name)
        self.print_and_log(f"键盘录制结果：{self.state}")
        self.push_record(None)

    def destroy_all(self):
        """销毁所有的子窗口"""
        self.dialog.destroy()
        self.prompt_label.destroy()
        self.info_bar.destroy()
        self.white_frame.destroy()
        self.black_frame.destroy()
        self.operate_table.destroy()
        self.record_table.destroy()
        self.destroy()

    def close(self):
        """结束截图"""
        if self.key_rec == False:
            self.closing = True
            self.white_frame.hide()
            self.black_frame.hide()
            # log截图窗口即将关闭
            self.logger.debug("截图窗口即将关闭")
            # operate_table中的"Esc"退出键行被选中并高亮
            self.operate_table.selectRow(4)
            # 重置窗口属性和类型
            # 设置窗口属性
            window_flags = QtCore.Qt.WindowFlags()
            window_flags |= QtCore.Qt.WindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
            )
            window_flags |= QtCore.Qt.WindowFlags(
                QtCore.Qt.WindowType.FramelessWindowHint
            )
            window_flags &= ~QtCore.Qt.WindowFlags(
                QtCore.Qt.WindowType.WindowTransparentForInput
            )
            # window_flags &= ~QtCore.Qt.WindowFlags(
            #     QtCore.Qt.WindowType.WindowDoesNotAcceptFocus
            # )
            window_flags &= ~QtCore.Qt.WindowFlags(
                QtCore.Qt.WindowType.WindowStaysOnTopHint
            )
            # 设置窗口类型
            window_type = QtCore.Qt.WindowType.Window
            # 合并窗口属性和窗口类型
            self.setWindowFlags(window_flags | window_type)
            # 发送对话信号
            self.have_dialog_signal.emit()

    def have_dialog(self):
        self.showFullScreen()
        # 创建一个QInputDialog实例
        self.dialog = QtWidgets.QInputDialog(self)
        # 设置窗口为frameless窗口
        self.dialog.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
            | QtCore.Qt.WindowType.Dialog
        )
        # 设置窗口字号大小
        self.dialog.setFont(QtGui.QFont("Microsoft YaHei UI", self.height() // 90))
        # 根据字号大小决定窗口大小
        self.dialog.adjustSize()
        # 设置窗口大小
        self.dialog.resize(
            self.dialog.width() + self.width() // 5,
            self.dialog.height() + self.height() // 5,
        )
        # 设置窗口位置，居中
        self.dialog.move(
            (self.width() - self.dialog.width()) // 2,
            self.height() // 2 - self.dialog.height(),
        )
        # 设置样式，标签和按钮的样式
        self.dialog.setStyleSheet(
            """
            QInputDialog {
                background-color: rgba(0, 0, 0, 128);
                color: white;
                border: 1px solid rgba(255, 255, 255, 128);
                padding: 5px;
            }
            QPushButton {
                background-color: rgba(0, 0, 0, 128);
                color: white;
                border: 1px solid rgba(255, 255, 255, 128);
                padding: 5px;
                font-family: "Microsoft YaHei UI";
            """
            + f"font-size: {pag.size()[1]//50}px;"
            + """
            }
            QLabel {
                color: white;
            }
            QInputDialog QLineEdit {
                background-color: rgba(0, 0, 0, 128);
                color: white;
                border: none;
                padding: 5px;
            }
            """
        )
        # 设置属性
        self.dialog.setInputMode(QtWidgets.QInputDialog.InputMode.TextInput)
        # 设置标题和标签
        self.dialog.setLabelText("请输入任务名称：\n-不应为空或与已有任务名称重复-")
        # 设置按钮
        self.dialog.setOkButtonText("确定(OK)")
        self.dialog.setCancelButtonText("继续截图(Continue)")
        # 创造一个新按钮
        quit_button = QtWidgets.QPushButton("退出(Quit)")
        # 设置按钮的样式
        quit_button.setStyleSheet(
            """
                background-color: rgba(0, 0, 0, 128);
                color: white;
                border: 1px solid rgba(255, 255, 255, 128);
                padding: 5px;
                font-family: "Microsoft YaHei UI";
            """
            + f"font-size: {pag.size()[1]//50}px;"
        )
        # 将新按钮添加到对话框中
        self.dialog.layout().addWidget(quit_button)
        # 为新按钮绑定事件
        quit_button.clicked.connect(self.dialog_quit)
        # 显示对话框
        self.dialog.show()
        # 显示对话框并获取结果
        self.ok = self.dialog.exec_()
        # log任务对话返回
        self.logger.debug(f"任务对话返回：{self.ok}")
        # 获取任务名称
        mission_name = self.dialog.textValue()
        # log任务名称
        self.logger.debug(f"任务名称：{mission_name}")

        # 处理对话结果
        if self.ok:
            # 检查任务名称是否为空
            if mission_name == "":
                # 提示任务名称不能为空
                self.set_prompt("任务名称不能为空")
                # log任务名称为空
                self.print_and_log("任务名称为空")
                # 重新显示对话框
                self.have_dialog_signal.emit()
            # 检查任务名称是否重复
            elif f"{mission_name}.csv" in os.listdir(f"{__BASE_DIR__}\\mission"):
                # 提示任务名称重复
                self.set_prompt("任务名称重复")
                # log任务名称重复
                self.print_and_log("任务名称重复")
                # 重新显示对话框
                self.have_dialog_signal.emit()
            else:
                # 截图归纳
                # 在screenshot_target创建{mission_name}文件夹
                os.mkdir(f"{__BASE_DIR__}\\screenshot_target\\{mission_name}")
                source = f"{__BASE_DIR__}\\screenshot_target"
                destination = f"{__BASE_DIR__}\\screenshot_target\\{mission_name}"
                # 从mission_dataframe中获取截图的绝对路径
                for file in self.mission_dataframe["截图"]:
                    # 如果截图的绝对路径不为空
                    if file != "" and isinstance(file, str):
                        # 获取截图的绝对路径
                        file_name = file.split("\\")[-1]
                        # 将截图移动到{mission_name}文件夹中
                        shutil.move(
                            f"{source}\\{file_name}", f"{destination}\\{file_name}"
                        )

                # 修改mission_dataframe的截图列
                for i in range(self.mission_dataframe.shape[0]):
                    # 获取截图的绝对路径
                    img_path = str(self.mission_dataframe.loc[i, "截图"])
                    # 如果截图的绝对路径不为空
                    if img_path != "":
                        # 修改截图的绝对路径，在screenshot_target后添加任务名称
                        last_part = img_path.split("\\")[-1]
                        new_last_part = f"{mission_name}\\{last_part}"
                        # 修改截图的绝对路径
                        self.mission_dataframe.loc[i, "截图"] = img_path.replace(
                            last_part, new_last_part
                        )
                # 保存任务
                self.mission_dataframe.to_csv(
                    f"{__BASE_DIR__}\\mission\\{mission_name}.csv", index=True
                )
                # log任务保存成功，保存地址
                self.logger.debug(
                    f"'{mission_name}'任务保存成功，保存地址：{__BASE_DIR__}\\mission\\{mission_name}.csv"
                )
                # 提示用户脚本创建成功
                self.set_prompt(f"'{mission_name}'脚本创建成功")
                # log脚本创建成功
                self.print_and_log(f"'{mission_name}'脚本创建成功")
                # 等待后结束程序
                if __name__ == "__main__":
                    self.ok = ""
                    QtCore.QTimer.singleShot(1000, QtWidgets.QApplication.quit)
                else:
                    self.go_back_to_auto()
        else:
            # 用户误操作
            if self.make_mistake:
                # log用户误操作
                self.logger.debug("用户误操作")
                self.closing = False
                self.white_frame.show()
                self.black_frame.show()
                self.update_position()
                # 重置窗口属性和类型
                # 设置窗口为全屏，无边框，背景透明，无法获取焦点（不会接收鼠标点击）
                self.setWindowFlags(
                    QtCore.Qt.WindowFlags()
                    | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
                    | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)
                    | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
                    | QtCore.Qt.WindowFlags(
                        QtCore.Qt.WindowType.WindowTransparentForInput
                    )
                    # | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.WindowDoesNotAcceptFocus)
                    | QtCore.Qt.WindowType.Window
                )
                # 提示用户继续截图
                self.set_prompt("请继续截图")
                # log用户继续截图
                self.print_and_log("用户继续截图")
                self.showFullScreen()

    def dialog_quit(self):
        """退出程序"""
        # 暂停其他事件处理
        QtWidgets.QApplication.processEvents()
        self.make_mistake = False
        # log用户退出程序
        self.logger.debug("用户退出程序")
        # 根据dataframe中的截图路径，删除截图
        for file in self.mission_dataframe["截图"]:
            # 如果截图的绝对路径不为空
            if file != "" and isinstance(file, str):
                # 删除截图
                os.remove(file)
        # 提示用户脚本创建失败
        self.set_prompt("脚本创建失败")
        self.print_and_log("脚本创建失败")
        # 等待后结束程序
        if __name__ == "__main__":
            QtCore.QTimer.singleShot(1000, QtWidgets.QApplication.quit)
        else:
            self.go_back_to_auto()

    def go_back_to_auto(self):
        self.ok = ""
        self.auto_caller.show()
        # 更新菜单列表
        self.auto_caller.reload_script_list()
        # log脚本重载：脚本列表
        self.logger.debug(f"脚本重载：{self.auto_caller.script_list}")
        self.auto_caller.update_menu_list()
        self.destroy_all()
        # 释放键盘钩子，防止键盘钩子重复而导致程序崩溃
        keyboard.unhook_all()
        # 鼠标监听线程停止
        self.mouse_listener.exit()

    def set_prompt(self, text: str) -> QtWidgets.QLabel:
        """设置提示信息"""
        # 设置标签的文本
        self.prompt_label.setText(text)
        # 调整标签的大小，使其能够正常显示文本
        self.prompt_label.adjustSize()
        # 高度和宽度分别增加窗口高度和宽度的1/30
        self.prompt_label.resize(
            self.prompt_label.width() + self.width() // 30,
            self.prompt_label.height() + self.height() // 30,
        )
        # 获取标签的高度和宽度
        p_height = self.prompt_label.height()
        p_width = self.prompt_label.width()
        if not self.closing:
            # 标签居中
            self.prompt_label.move(
                (self.width() - p_width) // 2, self.height() // 2 - p_height
            )
        else:
            self.prompt_label.move(
                (self.width() - p_width) // 2, self.height() // 2 + (p_height * 2)
            )
        # 弹窗显示管理
        rec1 = self.prompt_label.geometry()
        rec2 = self.white_frame.geometry()
        if rec1.intersects(rec2):
            self.prompt_label.hide()
        else:
            self.prompt_label.show()
            # 计时后隐藏标签
            QtCore.QTimer.singleShot(800, self.prompt_label.hide)

        return self.prompt_label

    def update_position(self):
        """更新截图区域的位置"""
        # self.print_and_log("正在更新截图区域的位置...")
        # 获取鼠标的位置
        cursor_pos = QtGui.QCursor.pos()
        # 移动色块到鼠标的位置
        pos = QtCore.QPoint(
            cursor_pos.x() - self.screenshot_area_width // 2,
            cursor_pos.y() - self.screenshot_area_height // 2,
        )
        if cursor_pos.x() + self.screenshot_area_width // 2 > self.width():
            pos.setX(self.width() - self.screenshot_area_width)
        if cursor_pos.y() + self.screenshot_area_height // 2 > self.height():
            pos.setY(self.height() - self.screenshot_area_height)
        if cursor_pos.x() - self.screenshot_area_width // 2 < 0:
            pos.setX(0)
        if cursor_pos.y() - self.screenshot_area_height // 2 < 0:
            pos.setY(0)
        self.screenshot_pos = pos
        self.white_frame.move(pos.x() - self.edge_width, pos.y() - self.edge_width)
        self.black_frame.move(
            pos.x() - self.edge_width * 2, pos.y() - self.edge_width * 2
        )
        self.screenshot_area_signal.emit(self.screenshot_pos)
        if not self.closing:
            # 每10毫秒后再次调用此函数
            QtCore.QTimer.singleShot(15, self.update_position)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    import missionAuto as ma

    test = ma.MissionAuto()
    test.hide()
    window = MissionCreate(test)
    sys.exit(app.exec_())
