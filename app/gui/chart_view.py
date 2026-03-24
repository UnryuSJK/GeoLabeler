import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QWidget, QGridLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from datetime import timedelta
import pandas as pd


class SingleChart(QWidget):
    """支持滚轮缩放、平移，并能【一键秒回】初始加载位置的单元"""

    def __init__(self, title, color, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # 1. 创建画布
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor='#2c3e50')
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#2c3e50')
        self.layout.addWidget(self.canvas)

        # 2. 创建刷新按钮
        self.reset_btn = QPushButton("↺", self.canvas)
        self.reset_btn.setFixedSize(32, 32)
        self.reset_btn.setToolTip("回到初始位置")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 152, 219, 180);
                color: white;
                border-radius: 16px;
                font-size: 20px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 255);
                border: 1px solid white;
            }
        """)
        self.reset_btn.clicked.connect(self.restore_initial_view)

        self.title = title
        self.color = color
        self.pressed = False

        # 核心：用于记录“刚加载出来时”的状态
        self.initial_xlim = None
        self.initial_ylim = None

        # 绑定交互事件
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('button_release_event', self.on_release)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)

        self.setup_ax()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reset_btn.move(self.canvas.width() - 42, 10)
        self.reset_btn.raise_()

    def setup_ax(self):
        self.ax.set_title(self.title, color='white', fontsize=10, fontweight='bold')
        self.ax.tick_params(colors='white', labelsize=8)
        self.ax.grid(True, linestyle=':', alpha=0.2)

    def restore_initial_view(self):
        """核心修复：直接跳回最初存下的那个位置"""
        if self.initial_xlim is not None and self.initial_ylim is not None:
            self.ax.set_xlim(self.initial_xlim)
            self.ax.set_ylim(self.initial_ylim)
            self.canvas.draw()

    def on_scroll(self, event):
        if event.inaxes != self.ax: return
        f = (1 / 1.25) if event.button == 'up' else 1.25
        cur_xlim, cur_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        new_w, new_h = (cur_xlim[1] - cur_xlim[0]) * f, (cur_ylim[1] - cur_ylim[0]) * f
        relx, rely = (cur_xlim[1] - event.xdata) / (cur_xlim[1] - cur_xlim[0]), (cur_ylim[1] - event.ydata) / (
                    cur_ylim[1] - cur_ylim[0])
        self.ax.set_xlim([event.xdata - new_w * (1 - relx), event.xdata + new_w * relx])
        self.ax.set_ylim([event.ydata - new_h * (1 - rely), event.ydata + new_h * rely])
        self.canvas.draw()

    def on_press(self, event):
        if event.inaxes != self.ax or event.button != 1: return
        self.pressed = True
        self.xpress, self.ypress = event.xdata, event.ydata

    def on_motion(self, event):
        if not self.pressed or event.inaxes != self.ax: return
        dx, dy = event.xdata - self.xpress, event.ydata - self.ypress
        self.ax.set_xlim(self.ax.get_xlim() - dx)
        self.ax.set_ylim(self.ax.get_ylim() - dy)
        self.canvas.draw()

    def on_release(self, event):
        self.pressed = False

    def update_data(self, df_raw, df_interp, col):
        self.ax.clear()
        self.setup_ax()

        # 绘图逻辑
        if col in df_interp.columns:
            self.ax.plot(df_interp['date'], df_interp[col], color=self.color, linewidth=2, zorder=2)
        if col in df_raw.columns:
            self.ax.scatter(df_raw['date'], df_raw[col], color='white', edgecolors=self.color, s=20, zorder=3)

        # 1. 先让 Matplotlib 自动计算一次最佳展示位置
        self.ax.relim()
        self.ax.autoscale_view()

        # 2. 稍微优化一下 Y 轴，别太挤
        y_min, y_max = self.ax.get_ylim()
        pad = (y_max - y_min) * 0.1
        self.ax.set_ylim(y_min - pad, y_max + pad)

        # 3. 【关键点】：记录下这时的“默认位置”
        self.canvas.draw()  # 必须先 draw 一下让坐标轴生效
        self.initial_xlim = self.ax.get_xlim()
        self.initial_ylim = self.ax.get_ylim()



class NDVIChart(QWidget):
    """四个独立交互单元的组合容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grid_layout = QGridLayout(self)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(5, 5, 5, 5)

        self.charts = {}
        # 定义布局配置：(行, 列, 字段名, 颜色)
        configs = [
            (0, 0, 'NDVI', '#2ecc71'), (0, 1, 'NDWI', '#3498db'),
            (1, 0, 'MNDWI', '#9b59b6'), (1, 1, 'LSWI', '#e67e22')
        ]

        for row, col, name, color in configs:
            chart_unit = SingleChart(name, color)
            self.grid_layout.addWidget(chart_unit, row, col)
            self.charts[name] = chart_unit

    def update_plot(self, data_dict):
        """
        接收数据字典并分发给各个子图
        data_dict: {"raw": DataFrame, "interp": DataFrame}
        """
        df_raw = data_dict["raw"]
        df_interp = data_dict["interp"]

        for name, chart in self.charts.items():
            chart.update_data(df_raw, df_interp, name)

    def show_message(self, text):
        print(f"Chart Status: {text}")