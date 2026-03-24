from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime
import calendar


class StyledDateFilter(QFrame):
    """
    三级联动下拉式日期筛选器 (年-月-日)
    替代原生窗口日历，支持自动计算单月天数
    """
    dateChanged = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DateFilterFrame")

        self.setStyleSheet("""
            #DateFilterFrame {
                background-color: #34495e;
                border-radius: 8px;
                border: 1px solid #455a64;
            }
            QLabel {
                color: #bdc3c7;
                font-size: 10px;
                font-weight: bold;
                margin-bottom: 2px;
                letter-spacing: 0.5px;
            }
            QComboBox {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #7f8c8d;
                border-radius: 4px;
                padding: 4px;
                min-width: 65px;
                font-size: 12px;
            }
            QComboBox:hover { border: 1px solid #3498db; }
            QComboBox::drop-down { border: none; width: 15px; }
            QComboBox QAbstractItemView {
                background-color: #2c3e50;
                color: white;
                selection-background-color: #3498db;
                outline: none;
            }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(15)

        # 准备数据范围
        this_year = datetime.now().year
        years = [str(y) for y in range(this_year - 15, this_year + 2)]
        months = [f"{m:02d}" for m in range(1, 13)]

        # --- 开始日期组 ---
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("FROM"))
        s_selectors = QHBoxLayout()
        self.s_year = QComboBox();
        self.s_year.addItems(years)
        self.s_month = QComboBox();
        self.s_month.addItems(months)
        self.s_day = QComboBox()
        s_selectors.addWidget(self.s_year);
        s_selectors.addWidget(self.s_month);
        s_selectors.addWidget(self.s_day)
        start_layout.addLayout(s_selectors)

        # --- 中间装饰 ---
        to_label = QLabel("▶")
        to_label.setStyleSheet("color: #3498db; font-size: 14px; margin-top: 15px;")

        # --- 结束日期组 ---
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("TO"))
        e_selectors = QHBoxLayout()
        self.e_year = QComboBox();
        self.e_year.addItems(years)
        self.e_month = QComboBox();
        self.e_month.addItems(months)
        self.e_day = QComboBox()
        e_selectors.addWidget(self.e_year);
        e_selectors.addWidget(self.e_month);
        e_selectors.addWidget(self.e_day)
        end_layout.addLayout(e_selectors)

        main_layout.addLayout(start_layout)
        main_layout.addWidget(to_label)
        main_layout.addLayout(end_layout)

        # 初始化默认值
        self.s_year.setCurrentText(str(this_year - 1))
        self.e_year.setCurrentText(str(this_year))
        self.s_month.setCurrentText("01")
        self.e_month.setCurrentText(datetime.now().strftime("%m"))

        # 初始填充天数
        self._update_days(self.s_year, self.s_month, self.s_day, 1)
        self._update_days(self.e_year, self.e_month, self.e_day, datetime.now().day)

        # 绑定联动逻辑
        self.s_year.currentIndexChanged.connect(lambda: self._update_days(self.s_year, self.s_month, self.s_day))
        self.s_month.currentIndexChanged.connect(lambda: self._update_days(self.s_year, self.s_month, self.s_day))
        self.e_year.currentIndexChanged.connect(lambda: self._update_days(self.e_year, self.e_month, self.e_day))
        self.e_month.currentIndexChanged.connect(lambda: self._update_days(self.e_year, self.e_month, self.e_day))

        # 绑定统一的变化信号
        for cb in [self.s_year, self.s_month, self.s_day, self.e_year, self.e_month, self.e_day]:
            cb.currentIndexChanged.connect(self._on_change)

    def _update_days(self, y_cb, m_cb, d_cb, default_day=None):
        """根据年月动态计算该月有多少天"""
        year = int(y_cb.currentText())
        month = int(m_cb.currentText())

        # 获取当前选中的日，防止重置丢失
        current_selected_day = d_cb.currentText()

        # 计算该月天数
        num_days = calendar.monthrange(year, month)[1]
        days = [f"{d:02d}" for d in range(1, num_days + 1)]

        d_cb.blockSignals(True)
        d_cb.clear()
        d_cb.addItems(days)

        # 恢复之前的选中项或设为默认
        if default_day:
            d_cb.setCurrentText(f"{default_day:02d}")
        elif current_selected_day in days:
            d_cb.setCurrentText(current_selected_day)
        else:
            d_cb.setCurrentIndex(d_cb.count() - 1)  # 如果选了31号切到2月，自动变28/29
        d_cb.blockSignals(False)

    def _on_change(self):
        s, e = self.get_dates()
        self.dateChanged.emit(s, e)

    def get_dates(self):
        """返回标准的 YYYY-MM-DD 格式字符串"""
        start = f"{self.s_year.currentText()}-{self.s_month.currentText()}-{self.s_day.currentText()}"
        end = f"{self.e_year.currentText()}-{self.e_month.currentText()}-{self.e_day.currentText()}"
        return start, end