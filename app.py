import sys
import os
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QFrame, QSizePolicy

from qfluentwidgets import (PrimaryPushButton, PushButton, RadioButton, TextEdit, 
                            SubtitleLabel, TitleLabel, MSFluentWindow,
                            setTheme, Theme, CardWidget, SimpleCardWidget, FluentIcon,
                            InfoBar, InfoBarPosition)

class AspectRatioLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(100, 100)
        self._original_pixmap = QPixmap()
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #f0f0f0; border-radius: 8px;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def setPixmap(self, pixmap):
        self._original_pixmap = pixmap
        self.update_pixmap()

    def update_pixmap(self):
        if not self._original_pixmap.isNull():
            scaled = self._original_pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            super().setPixmap(scaled)

    def resizeEvent(self, event):
        self.update_pixmap()
        super().resizeEvent(event)

from test_color import run_color_test
from test_label import run_label_test

class MainInterface(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainInterface")
        
        # Main Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # --- Left Panel ---
        self.left_panel = QFrame(self)
        self.left_panel.setFixedWidth(300)
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(15)
        
        # Title
        self.title_label = TitleLabel("质检控制台", self)
        
        # Card 1: Mode Selection
        self.mode_card = SimpleCardWidget(self)
        self.mode_layout = QVBoxLayout(self.mode_card)
        self.mode_layout.setContentsMargins(20, 20, 20, 20)
        
        self.mode_title = SubtitleLabel("① 选择检测模式", self)
        self.radio_color = RadioButton("服装色差等级评估", self)
        self.radio_color.setChecked(True)
        self.radio_label = RadioButton("标签对齐与缺陷检测", self)
        
        self.mode_layout.addWidget(self.mode_title)
        self.mode_layout.addSpacing(10)
        self.mode_layout.addWidget(self.radio_color)
        self.mode_layout.addSpacing(5)
        self.mode_layout.addWidget(self.radio_label)
        
        # Card 2: Image Selection
        self.image_card = SimpleCardWidget(self)
        self.image_layout = QVBoxLayout(self.image_card)
        self.image_layout.setContentsMargins(20, 20, 20, 20)
        
        self.image_title = SubtitleLabel("② 导入检测样本", self)
        self.btn_select = PushButton(FluentIcon.FOLDER, "选择拼接图片", self)
        self.btn_select.clicked.connect(self.select_image)
        
        self.path_label = QLabel("未选择文件...", self)
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #666;")
        
        self.image_layout.addWidget(self.image_title)
        self.image_layout.addSpacing(10)
        self.image_layout.addWidget(self.btn_select)
        self.image_layout.addSpacing(5)
        self.image_layout.addWidget(self.path_label)
        
        # Run Button
        self.btn_run = PrimaryPushButton(FluentIcon.PLAY, "开始智能检测", self)
        self.btn_run.setFixedHeight(45)
        font = self.btn_run.font()
        font.setPointSize(12)
        font.setBold(True)
        self.btn_run.setFont(font)
        self.btn_run.clicked.connect(self.run_test)
        
        # Assemble Left
        self.left_layout.addWidget(self.title_label)
        self.left_layout.addSpacing(10)
        self.left_layout.addWidget(self.mode_card)
        self.left_layout.addWidget(self.image_card)
        self.left_layout.addStretch(1)
        self.left_layout.addWidget(self.btn_run)
        
        # --- Right Panel (Results) ---
        self.right_panel = SimpleCardWidget(self)
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(20, 20, 20, 20)
        
        self.res_title = SubtitleLabel("可视化检测结果", self)
        
        # Image View
        self.img_view = AspectRatioLabel(self)
        
        # Text Result
        self.text_result = TextEdit(self)
        self.text_result.setReadOnly(True)
        self.text_result.setFixedHeight(120)
        self.text_result.setPlaceholderText("检测报告将在此处显示...")
        
        # Assemble Right
        self.right_layout.addWidget(self.res_title)
        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.img_view, 1)
        self.right_layout.addSpacing(10)
        self.right_layout.addWidget(self.text_result)
        
        # Assemble Main
        self.main_layout.addWidget(self.left_panel)
        self.main_layout.addWidget(self.right_panel, 1)
        
        self.current_image_path = None

    def select_image(self):
        # Open in the tests directory by default
        initial_dir = os.path.abspath(r'color_tests') if self.radio_color.isChecked() else os.path.abspath(r'label_tests')
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择拼接图片", initial_dir, "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.current_image_path = file_path
            filename = os.path.basename(file_path)
            self.path_label.setText(f"已选择: {filename}")
            self.show_image(file_path)
            self.text_result.clear()

    def show_image(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.img_view.setPixmap(pixmap)

    def run_test(self):
        if not self.current_image_path:
            InfoBar.warning(
                title='提示',
                content='请先选择一张待测图片',
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return
            
        self.btn_run.setText("检测中...")
        self.btn_run.setEnabled(False)
        self.text_result.setText("正在执行深度学习算法，请稍候...")
        QApplication.processEvents() # Force UI update
        
        try:
            if self.radio_color.isChecked():
                out_img, res_text = run_color_test(self.current_image_path)
            else:
                out_img, res_text = run_label_test(self.current_image_path)
                
            if out_img:
                # Update current image path so it resizes correctly
                self.current_image_path = out_img
                self.show_image(out_img)
            self.text_result.setText(f"✅ 检测完成：\n\n{res_text}")
        except Exception as e:
            self.text_result.setText(f"❌ 发生错误:\n{str(e)}")
        finally:
            self.btn_run.setText("开始智能检测")
            self.btn_run.setEnabled(True)

class App(MSFluentWindow):
    def __init__(self):
        super().__init__()
        self.resize(1000, 700)
        self.setWindowTitle('基于人工智能的服装成衣质量检测平台')
        
        # Set to LIGHT theme
        setTheme(Theme.LIGHT)
        
        self.main_interface = MainInterface()
        self.addSubInterface(self.main_interface, FluentIcon.HOME, '智能质检中心')

if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    w = App()
    w.show()
    sys.exit(app.exec())
