import ee
import os
import sys

# --- 核心修复：强制禁用所有硬件加速和沙盒模式 ---
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --no-sandbox"
# 告诉 Qt 禁用合成渲染器
os.environ["QT_XCB_GL_INTEGRATION"] = "none"

# ... 其余导入
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from app.gui.main_window import MainWindow
from app.gui.auth_dialog import GEEAuthDialog  # 导入刚才写的对话框



def run_gee_auth_flow():
    """
    带 GUI 交互的认证流程
    """
    try:
        # 尝试直接初始化
        ee.Initialize()
        return True
    except Exception:
        # 获取认证 URL (注意这里不直接调用 Authenticate)
        try:
            # 获取授权链接
            auth_url = ee.oauth.get_authorization_url()

            # 弹出对话框
            dialog = GEEAuthDialog(auth_url)
            if dialog.exec_() == GEEAuthDialog.Accepted:
                verification_code = dialog.auth_code
                # 使用用户输入的 code 完成认证
                ee.Authenticate(authorization_code=verification_code)
                ee.Initialize()
                return True
        except Exception as e:
            print(f"认证失败: {e}")
            return False
    return False


def main():
    # 启用高 DPI (针对 4K 屏优化)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 执行 GUI 认证流程
    if not run_gee_auth_flow():
        QMessageBox.warning(None, "GEE 授权", "未能完成 GEE 授权，部分功能（如 NDVI 曲线）可能无法使用。")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()