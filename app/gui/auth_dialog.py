from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt
import webbrowser

class GEEAuthDialog(QDialog):
    def __init__(self, auth_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Google Earth Engine 首次授权")
        self.setFixedSize(450, 200)
        self.auth_code = None
        self.url = auth_url
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        label = QLabel("检测到尚未授权 GEE。请点击下方按钮打开浏览器，\n登录并复制验证码，然后粘贴到输入框中：")
        label.setWordWrap(True)
        layout.addWidget(label)

        # 按钮：打开浏览器
        btn_open = QPushButton("1. 点击打开浏览器登录")
        btn_open.clicked.connect(lambda: webbrowser.open(self.url))
        layout.addWidget(btn_open)

        # 输入框
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("在此粘贴验证码 (Verification Code)...")
        layout.addWidget(self.line_edit)

        # 确认按钮
        btn_confirm = QPushButton("2. 完成授权")
        btn_confirm.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        btn_confirm.clicked.connect(self.handle_confirm)
        layout.addWidget(btn_confirm)

    def handle_confirm(self):
        code = self.line_edit.text().strip()
        if code:
            self.auth_code = code
            self.accept() # 关闭对话框并返回成功状态