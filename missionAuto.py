import os
import sys
import shutil
import threading
import inspect
import pandas as pd
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import pyautogui as pag
import tabulate

from __init__ import __BASE_DIR__, logger
from wcwidth import wcswidth


class MissionAuto(QtWidgets.QWidget):
    """任务自动化类"""

    def __init__(self):
        super().__init__()

        # 属性设置
        self.selected_script = QtWidgets.QListWidgetItem()
        self.script_list = []
        self.lock = threading.Lock()
        self.script_df = pd.DataFrame()
        self.logger = logger

        # log框型注释：新的运行开始了！
        self.print_and_log(
            """\n
            ******************************\n
            * MissionAuto：新的运行开始了！*\n
            ******************************
            """
        )

        # 初始化UI
        self.init_ui()

        # 任务选择器，选择存在的任务脚本
        self.mission_picker()

    def init_ui(self):
        """初始化UI"""
        # 参数设置
        self.common_space = pag.size()[1] // 50
        self.common_font_size = pag.size()[1] // 45

        # 控件设置
        self.main_widget = QtWidgets.QWidget(self)
        self.title_label = QtWidgets.QLabel("请选择你要执行的任务脚本")
        self.menu_list = QtWidgets.QListWidget()
        self.select_script_button = QtWidgets.QPushButton("执行任务")
        self.script_record_button = QtWidgets.QPushButton("录制任务")
        self.script_edit_button = QtWidgets.QPushButton("编辑任务")
        self.script_delete_button = QtWidgets.QPushButton("删除任务")
        self.quit_program_button = QtWidgets.QPushButton("退出程序")
        self.minimize_program_button = QtWidgets.QPushButton("最小化")
        self.vbox = QtWidgets.QVBoxLayout()
        self.hbox = QtWidgets.QHBoxLayout()
        self.prompt_label = QtWidgets.QLabel(self)

        # 设置父窗口属性
        self.setWindowFlags(
            QtCore.Qt.WindowFlags()
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.CustomizeWindowHint)
            | QtCore.Qt.WindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(pag.size()[0], pag.size()[1])

        # 设置提示标签属性
        font = QtGui.QFont()
        font.setFamilies(["Microsoft YaHei UI"])
        self.prompt_label.setFont(font)
        self.prompt_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.prompt_label.hide()

        # 设置控件大小位置
        # 设置主窗口大小
        self.main_widget.resize(pag.size()[0] // 2, pag.size()[1] // 2)
        # 设置窗口居中
        self.main_widget.move(
            pag.size()[0] // 2 - self.main_widget.width() // 2,
            pag.size()[1] // 2 - self.main_widget.height() // 2,
        )

        # 设置控件样式表
        self.main_widget.setStyleSheet(
            """
            QWidget{
                background-color: rgba(0, 0, 0, 128);
            }
            QPushButton{
                background-color: rgba(0, 0, 0, 128);
                font-family: "Microsoft YaHei UI";
            """
            + f"font-size: {self.common_font_size}px;"
            + """
                color: white;
                border: 1px solid white;
                padding: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 255); 
                color: black; 
                border: 1px solid white;
            }
            """
        )

        self.title_label.setStyleSheet(
            """
            QLabel{
                background-color: rgba(0, 0, 0, 128);
            """
            + f"font-size: {self.common_font_size}px;"
            + """
                font-family: "Microsoft YaHei UI";
                color: white;
                padding: 10px;
            }
            """
        )

        self.menu_list.setStyleSheet(
            """
            QListWidget{
                background-color: rgba(0, 0, 0, 128);
                color: white;
            """
            + f"font-size: {self.common_font_size}px;"
            + """
                border: 2px solid white;
                padding: 10px;
            }
            QListWidget::item:hover {
                background-color: rgba(0, 51, 204, 128); 
                color: white; 
                border: none;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 51, 204, 128); 
                color: white; 
                border: 1px solid white;
            }
            """
        )

        self.prompt_label.setStyleSheet(
            f"font-size:{pag.size()[1]//50}px;color: white;background-color: rgba(0,0,0,128);"
        )

        # 按顺序添加控件
        # 将标题标签添加到垂直布局中
        self.vbox.addWidget(self.title_label)
        # 将菜单列表添加到垂直布局中
        self.vbox.addWidget(self.menu_list)
        # 将水平布局添加到垂直布局中
        self.vbox.addLayout(self.hbox)
        # 将按钮添加到水平布局中
        self.hbox.addWidget(self.select_script_button)
        self.hbox.addWidget(self.script_record_button)
        self.hbox.addWidget(self.script_edit_button)
        self.hbox.addWidget(self.script_delete_button)
        self.hbox.addWidget(self.quit_program_button)
        self.hbox.addWidget(self.minimize_program_button)
        # 将垂直布局添加到窗口中
        self.main_widget.setLayout(self.vbox)

        # 显示窗口
        self.show()

        # # 设置 Pandas 打印选项
        # pd.set_option("display.max_colwidth", None)  # 取消内容截断
        # pd.set_option("display.colheader_justify", "left")  # 表头左对齐

    def print_and_log(self, text: str):
        """打印并记录日志"""
        print(text)
        caller_frame = inspect.stack()[1]
        caller_line = caller_frame.lineno
        self.logger.debug(f"{text}\n(Called at line {caller_line})")

    def mission_picker(self):
        """任务选择器，选择存在的任务脚本"""
        # 检查__BASE_DIR__中mission文件夹，获取其中的csv脚本文件列表
        self.reload_script_list()
        # log脚本重载：脚本列表
        self.print_and_log(f"脚本重载：{self.script_list}")

        # 当用户点击退出程序按钮时，退出程序
        self.quit_program_button.clicked.connect(self.quit_program)
        # 当用户点击最小化程序按钮时，最小化程序
        self.minimize_program_button.clicked.connect(self.showMinimized)
        # 当用户点击录制新的脚本按钮时，录制新的脚本
        self.script_record_button.clicked.connect(self.script_record)
        self.script_related_button_connect(self.create_or_select_first)

        # 如果不存在脚本，提示用户创建脚本
        if self.script_list == []:
            self.set_prompt("不存在脚本，请创建脚本")
            self.print_and_log("不存在脚本，请创建脚本")
        else:
            # 更新菜单列表
            self.update_menu_list()

        # 为菜单列表中的每一项添加点击事件
        # 不可以将本语句放在update_menu_list()中，否则会出现重复
        self.menu_list.itemClicked.connect(self.wait_for_operation)

    def reload_script_list(self):
        # 清空脚本列表
        self.script_list.clear()
        # 检查__BASE_DIR__中mission文件夹，获取其中的csv脚本文件列表
        for file in os.listdir(os.path.join(__BASE_DIR__, "mission")):
            if file.endswith(".csv"):
                self.script_list.append(file)

    def update_menu_list(self):
        """更新菜单列表"""
        # 清除菜单列表中的所有项
        self.menu_list.clear()
        # 将脚本列表添加到菜单列表中
        self.menu_list.addItems(self.script_list)

    def create_or_select_first(self):
        """提示用户创建脚本或选择一个脚本"""
        if self.script_list == []:
            self.set_prompt("不存在脚本，请创建脚本")
            self.print_and_log("不存在脚本，请创建脚本")
        elif self.selected_script.text() == "" and self.script_list != []:
            self.set_prompt("请先选择一个任务脚本")
            self.print_and_log("请先选择一个任务脚本")

    def script_related_button_connect(self, connect_func):
        """为脚本相关按钮添加点击事件"""
        self.select_script_button.clicked.connect(connect_func)
        self.script_edit_button.clicked.connect(connect_func)
        self.script_delete_button.clicked.connect(connect_func)

    def wait_for_operation(self):
        """等待用户操作"""
        # 获取用户选择的脚本
        self.selected_script = self.menu_list.currentItem()
        # log用户选择的脚本：脚本名称
        self.print_and_log(f"用户选择的脚本：{self.selected_script.text()}")

        # 为按钮添加点击事件
        self.select_script_button.clicked.connect(self.auto_mission)
        self.script_edit_button.clicked.connect(self.script_edit)
        self.script_delete_button.clicked.connect(self.script_delete)

    def auto_mission(self):
        """执行用户选择的脚本"""
        # 对话窗口最小化
        self.showMinimized()
        # 如果没有选择脚本，函数无法执行
        if self.selected_script.text() == "":
            return
        # log执行用户选择的脚本：脚本名称
        self.print_and_log(f"执行用户选择的脚本：{self.selected_script.text()}")
        # 根据脚本名称，读取脚本文件，获取脚本内容转为dataframe
        with open(
            os.path.join(__BASE_DIR__, "mission", self.selected_script.text()), "r"
        ) as f:
            script_df = pd.read_csv(f, index_col=0, encoding="utf-8")
            # 将状态列的列表字符串转为列表
            script_df["状态"] = script_df["状态"].apply(lambda x: eval(x))
            # 格式化脚本dataframe
            formated_script_df = self.formated_dataframe(script_df)
            # log脚本内容：脚本内容
            self.print_and_log(
                f"\n脚本内容：\n{tabulate.tabulate(formated_script_df.values.tolist(), headers=formated_script_df.columns.tolist(), tablefmt='psql')}\n"
            )
            # 解释脚本内容，并执行
            self.mission_interpreter(script_df=script_df)

    def formated_dataframe(self, script_df: pd.DataFrame) -> pd.DataFrame:
        """将脚本dataframe格式化"""
        # 取出脚本dataframe的副本
        formated_script_df = script_df.copy()
        # 规定每一列的最大宽度
        max_widths = {"操作": 25, "截图": 20, "状态": 25, "后续": 35}
        # 根据最大宽度，将脚本dataframe的每一列格式化
        for col, max_width in max_widths.items():
            formated_script_df[col] = formated_script_df[col].apply(
                lambda x: str(x)[: max_width - wcswidth(str(x)) + len(str(x)) - 3]
                + "..."
                if wcswidth(str(x)) > max_width
                else str(x)[: max_width - wcswidth(str(x)) + len(str(x))]
            )
        # 返回格式化后的脚本dataframe
        return formated_script_df

    def mission_interpreter(self, script_df: pd.DataFrame):
        """解释脚本内容，并执行"""
        print("开始执行脚本")
        time_interval = 1
        # 遍历脚本每行内容
        for _, record in script_df.iterrows():
            self.print_and_log(f"当前操作：\n{record}\n")
            match record["操作"]:
                case "左键单击":
                    # self.print_and_log("左键单击")
                    while True:
                        # 根据截图路径，定位坐标，和截图有90%的相似度即认为匹配成功
                        button_position_1 = pag.locateCenterOnScreen(record["截图"], confidence=0.9)  # type: ignore
                        # 如果没有找到截图，重新定位坐标
                        for i in range(30):
                            if button_position_1 is not None:
                                break

                            self.set_prompt("未找到截图，重新定位坐标，第{}/30次".format(i + 1))
                            # log未找到截图，重新定位坐标，第i+1次
                            self.print_and_log("未找到截图，重新定位坐标，第{}/30次".format(i + 1))
                            # 间隔0.5秒，重新定位坐标
                            pag.sleep(0.5)
                            button_position_1 = pag.locateCenterOnScreen(record["截图"])  # type: ignore

                            if i == 29 and button_position_1 is None:
                                self.set_prompt("根据截图定位失败，请确保截图中的按钮在屏幕中")
                                self.print_and_log("根据截图定位失败，请确保截图中的按钮在屏幕中")
                                self.quit_program()

                        # 根据坐标，点击鼠标
                        pag.moveTo(
                            button_position_1[0],
                            button_position_1[1],
                            duration=time_interval,
                        )
                        # 由于网页加载等原因，可能会导致页面元素偏移，因此需要校对坐标
                        button_position_2 = pag.locateCenterOnScreen(record["截图"], confidence=0.9)  # type: ignore
                        # 比较两次截图的坐标是否相同，如果不同，重新定位坐标
                        if button_position_1 != button_position_2:
                            self.print_and_log("页面元素发生移动，重新定位坐标")
                        else:
                            break

                    pag.click(
                        button="left", x=button_position_1[0], y=button_position_1[1]
                    )

                case "左键双击":
                    # self.print_and_log("左键双击")
                    x_pos, y_pos = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval / 50)
                    pag.click(button="left", x=x_pos, y=y_pos)
                case "右键单击":
                    # self.print_and_log("右键单击")
                    x_pos, y_pos = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval)
                    pag.click(button="right", x=x_pos, y=y_pos)
                case "左键长按":
                    # self.print_and_log("左键长按")
                    x_pos, y_pos, duration = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval)
                    pag.mouseDown(
                        button="left", x=x_pos, y=y_pos, duration=duration + 0.5
                    )
                case "右键长按":
                    # self.print_and_log("右键长按")
                    x_pos, y_pos, duration = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval)
                    pag.mouseDown(
                        button="right", x=x_pos, y=y_pos, duration=duration + 0.5
                    )
                case "左键释放":
                    # self.print_and_log("左键释放")
                    x_pos, y_pos = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval / 50)
                    pag.mouseUp(button="left", x=x_pos, y=y_pos)
                case "右键释放":
                    # self.print_and_log("右键释放")
                    x_pos, y_pos = record["状态"]
                    pag.moveTo(x_pos, y_pos, duration=time_interval / 50)
                    pag.mouseUp(button="right", x=x_pos, y=y_pos)
                case "滚轮":
                    # self.print_and_log("滚轮")
                    x_pos, y_pos, x_scroll, y_scroll = record["状态"]
                    pag.scroll(x_scroll, y_scroll, x_pos, y_pos)
                case "键盘录制结果":
                    # self.print_and_log("输出键盘录制结果")
                    key_events = record["状态"][:-3]
                    for key_event in key_events:
                        pag.press(key_event)

        self.print_and_log("脚本执行完毕")

    def script_record(self):
        """录制新的脚本"""
        import missionCreate as mc

        # log录制新的脚本
        self.print_and_log("录制新的脚本")
        self.hide()

        # 创建新的MissionCreate对象
        self.mission_creator = mc.MissionCreate(global_mission_auto)

    def script_edit(self):
        """编辑已经存在的脚本"""
        # 如果没有选择脚本，函数无法执行
        if self.selected_script.text() == "":
            return

        # log编辑脚本：脚本名称
        self.print_and_log(f"编辑脚本：{self.selected_script.text()}")
        # 打开脚本文件
        os.system(
            f"{os.path.join(__BASE_DIR__, 'mission', self.selected_script.text())}"
        )

    def script_delete(self):
        """删除已经存在的脚本"""
        # 如果没有选择脚本，函数无法执行
        if self.selected_script.text() == "":
            return

        # 删除mission文件夹中对应csv脚本文件
        os.remove(os.path.join(__BASE_DIR__, "mission", self.selected_script.text()))
        # log脚本从mission文件夹中删除：脚本名称
        self.print_and_log(f"脚本从mission文件夹中删除：{self.selected_script.text()}")
        # 检查相应的截图文件夹是否存在，如果存在，删除
        screenshot_file_path = os.path.join(
            __BASE_DIR__,
            "screenshot_target",
            self.selected_script.text().split(".")[0],
        )
        if os.path.exists(screenshot_file_path):
            # 删除screenshot_target文件夹中对应的截图文件夹
            shutil.rmtree(screenshot_file_path)
        # log脚本截图文件夹从screenshot_target文件夹中删除：脚本名称
        self.print_and_log(
            f"脚本截图文件夹从screenshot_target文件夹中删除：{self.selected_script.text().split('.')[0]}"
        )

        # 删除菜单列表中的脚本
        self.menu_list.takeItem(self.menu_list.row(self.selected_script))
        # 更新self.script_list
        self.script_list.remove(self.selected_script.text())
        # log脚本从菜单列表中删除：脚本名称
        self.print_and_log(f"脚本从菜单列表中删除：{self.selected_script.text()}")
        # 清空self.selected_script
        self.selected_script = QtWidgets.QListWidgetItem()

    def quit_program(self):
        """退出程序"""
        # log退出程序
        self.print_and_log("退出程序")
        # 退出程序
        QtCore.QCoreApplication.quit()

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

        # 标签居中
        self.prompt_label.move(
            (self.width() - p_width) // 2, self.height() // 2 - p_height
        )

        # 显示标签
        self.prompt_label.show()
        # 1秒后隐藏标签
        QtCore.QTimer.singleShot(1000, self.prompt_label.hide)

        return self.prompt_label


if __name__ == "__main__":
    print("开始调试")
    app = QtWidgets.QApplication(sys.argv)
    # 创建一个全局的MissionAuto实例
    global_mission_auto = MissionAuto()
    sys.exit(app.exec_())
