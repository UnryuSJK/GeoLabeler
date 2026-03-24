import os
import sys
import webbrowser
import json
from pathlib import Path

# --- 核心修复：Qt 环境兼容性 ---
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --no-sandbox"
os.environ["QT_XCB_GL_INTEGRATION"] = "none"

import ee
from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog
from PyQt5.QtCore import Qt

# 导入你的主窗口
from app.gui.main_window import MainWindow

# --- 配置文件路径管理 ---
# 确保 config 文件夹存在
CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(exist_ok=True)  # 如果不存在则自动创建
CONFIG_FILE = CONFIG_DIR / "gee_config.json"


def load_gee_config():
    """从 config/gee_config.json 读取项目 ID"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("project_id")
        except Exception as e:
            print(f"读取配置文件出错: {e}")
    return None


def save_gee_config(project_id):
    """将项目 ID 保存到 config/gee_config.json"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({"project_id": project_id}, f, indent=4)
    except Exception as e:
        print(f"配置文件保存失败: {e}")


def run_gee_auth_flow():
    """
    带持久化配置的 GEE 认证逻辑
    """
    # 1. 优先加载本地配置
    project_id = load_gee_config()

    # 2. 尝试带 ID 初始化
    try:
        if project_id:
            # 如果有 ID，尝试静默初始化
            ee.Initialize(project=project_id)
            print(f"✅ GEE 初始化成功 (项目: {project_id})")
            return True
    except Exception as e:
        print(f"🔍 初始尝试失败 (可能未认证或 ID 失效): {e}")

    # 3. 授权与引导流程
    try:
        # A. 浏览器 OAuth 认证 (localhost 模式)
        QMessageBox.information(None, "GEE 首次授权",
                                "程序将打开浏览器进行 Google 账号授权。\n授权完成后请回到本软件。")
        ee.Authenticate(auth_mode='localhost', quiet=True)

        # B. 引导获取 Project ID
        webbrowser.open("https://code.earthengine.google.com/")

        # C. 弹出对话框
        text, ok = QInputDialog.getText(
            None,
            "配置 GEE 项目 ID",
            "已为您打开 GEE 官网，请在网页右上角找到 Project ID 并填入：\n"
            "(通常格式为: ee-yourname 或 project-123456)"
        )

        if ok and text.strip():
            new_id = text.strip()
            # D. 尝试用新 ID 初始化
            ee.Initialize(project=new_id)
            # E. 成功后保存到 config 目录
            save_gee_config(new_id)
            QMessageBox.information(None, "成功", f"配置已保存！\n项目 ID: {new_id}")
            return True
        else:
            return False

    except Exception as auth_e:
        QMessageBox.critical(None, "认证失败", f"流程中途出错: {auth_e}")
        return False


def main():
    # 适配高 DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 执行 GEE 认证/配置流程
    # 注意：如果认证失败，我们依然允许进入主界面，但会弹警告
    if not run_gee_auth_flow():
        QMessageBox.warning(None, "GEE 未就绪",
                            "您未完成授权或项目配置。\nNDVI 提取等在线功能将无法使用。")

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()