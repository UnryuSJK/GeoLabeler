import sys
from PyQt5.QtWidgets import (QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QFileDialog, QSplitter,
                             QApplication, QMessageBox)
from PyQt5.QtCore import Qt, QAbstractTableModel, QVariant

# 导入组件
from app.gui.widgets import StyledDateFilter
from app.core.gee_extractor import NDVIFetcher
from app.core.vector_io import VectorDataManager
from app.gui.chart_view import NDVIChart
from app.gui.map_canvas import MapCanvas


class FastGeomModel(QAbstractTableModel):
    def __init__(self, gdf, main_window=None):
        super().__init__()
        self._gdf = gdf
        self.main_window = main_window  # 传入窗口引用，方便修改标题
        # --- 重排列顺序 ---
        all_cols = [c for c in gdf.columns if c != 'geometry']

        # 如果列中包含 u_label，则将其移动到最前面
        target_col = 'u_label'
        if target_col in all_cols:
            all_cols.remove(target_col)
            all_cols.insert(0, target_col)

        self._cols = all_cols
        # -----------------------

    def rowCount(self, parent=None):
        return len(self._gdf)

    def columnCount(self, parent=None):
        return len(self._cols)

    def flags(self, index):
        # 核心：必须加上 ItemIsEditable 才能双击修改
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return QVariant()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            val = self._gdf.iloc[index.row()][self._cols[index.column()]]
            return str(val)
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        """当用户改完按回车时，触发这个函数"""
        if index.isValid() and role == Qt.EditRole:
            row = index.row()
            col_name = self._cols[index.column()]

            try:
                # 1. 自动转换类型（保持与原数据类型一致）
                old_val = self._gdf.iloc[row][col_name]
                casted_value = type(old_val)(value)

                # 2. 更新内存里的 GDF
                self._gdf.at[row, col_name] = casted_value

                # 3. 标记脏数据，通知主窗口改标题
                if self.main_window:
                    self.main_window.is_dirty = True
                    self.main_window.setWindowTitle("GeoLabeler (Unsaved Changes*)")

                # 4. 通知界面刷新该单元格
                self.dataChanged.emit(index, index, [role])
                return True
            except Exception as e:
                print(f"Update error: {e}")
                return False
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._cols[section])
            return str(section + 1)
        return QVariant()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoLabeler")
        self.resize(1200, 800)

        self.data_manager = VectorDataManager()
        self.active_fetcher = None
        self.is_dirty = False

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧面板 ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("📂 Upload SHP")
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setStyleSheet("background-color: #27ae60; color: white;")
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save)

        # 修改点：使用 QTableView
        self.table = QTableView()
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.setAlternatingRowColors(True)  # 让大数据量更易读

        self.btn_load.clicked.connect(self.on_load_clicked)
        self.btn_save.clicked.connect(self.on_save_clicked)

        left_layout.addLayout(btn_layout)
        left_layout.addWidget(self.table)

        # --- 右侧面板 ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.date_filter = StyledDateFilter()
        self.map_view = MapCanvas(self)
        self.chart_view = NDVIChart(self)

        right_layout.addWidget(self.date_filter)
        right_layout.addWidget(self.map_view, stretch=2)
        right_layout.addWidget(self.chart_view, stretch=3)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        layout.addWidget(splitter)
        splitter.setSizes([400, 800])

    def clear_active_fetcher(self):
        if self.active_fetcher and self.active_fetcher.isRunning():
            try:
                self.active_fetcher.finished.disconnect()
                self.active_fetcher.error.disconnect()
            except:
                pass
            self.active_fetcher.terminate()
            self.active_fetcher.wait(300)
        self.active_fetcher = None

    def on_selection_changed(self):
        """适配 QTableView 的选择逻辑"""
        if self.data_manager.gdf is None or self.data_manager.gdf.empty:
            return

        indexes = self.table.selectionModel().selectedRows()
        if not indexes: return

        idx = indexes[0].row()
        self.clear_active_fetcher()

        point = self.data_manager.gdf.iloc[idx].geometry
        self.map_view.plot_gdf(self.data_manager.gdf, highlight_idx=idx, auto_zoom=True)
        self.chart_view.show_message("Extracting NDVI from GEE...")

        start, end = self.date_filter.get_dates()
        self.active_fetcher = NDVIFetcher(point.x, point.y, start, end)
        self.active_fetcher.finished.connect(self.chart_view.update_plot)
        self.active_fetcher.error.connect(self.chart_view.show_message)
        self.active_fetcher.start()

    def on_load_clicked(self):
        self.clear_active_fetcher()

        # 1. 询问保存逻辑
        if self.data_manager.gdf is not None and not self.data_manager.gdf.empty:
            if not self.maybe_save_prompt():
                return

        path, _ = QFileDialog.getOpenFileName(self, "Select SHP", "", "Shapefile (*.shp)")
        if path:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.chart_view.show_message("⌛ Processing points...")
            QApplication.processEvents()

            try:
                # 2. 彻底解绑旧 Model，防止信号残留
                self.table.setModel(None)

                # 3. 加载数据
                new_gdf = self.data_manager.load_shapefile(path)
                self.data_manager.gdf = new_gdf

                # 4. 绑定新 Model (秒开的关键)
                model = FastGeomModel(new_gdf)
                self.table.setModel(model)

                # 5. 连接选择信号 (TableView 的选择信号是在 selectionModel 里的)
                self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)

                # 6. 地图性能保护：如果点数太多，抽样显示
                point_count = len(new_gdf)
                display_gdf = new_gdf.head(2000) if point_count > 2000 else new_gdf
                self.map_view.plot_gdf(display_gdf, auto_zoom=(point_count < 3000))

                self.setWindowTitle(f"GeoLabeler - {point_count} Points Loaded")
                self.is_dirty = False

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Load failed: {e}")
            finally:
                QApplication.restoreOverrideCursor()

    def maybe_save_prompt(self):
        msg = QMessageBox(self)
        msg.setText("Do you want to save changes before loading new SHP?")
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.No | QMessageBox.Cancel)
        res = msg.exec_()
        if res == QMessageBox.Cancel: return False
        if res == QMessageBox.Save: return self.on_save_clicked()
        return True

    def on_save_clicked(self):
        if self.data_manager.gdf is None: return False
        save_path, _ = QFileDialog.getSaveFileName(self, "Save SHP", "", "Shapefile (*.shp)")
        if save_path:
            try:
                self.data_manager.gdf.to_file(save_path)
                self.is_dirty = False
                return True
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        return False

    def closeEvent(self, event):
        self.clear_active_fetcher()
        event.accept()

