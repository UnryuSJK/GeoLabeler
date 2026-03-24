import os
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class MapCanvas(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_path = os.path.abspath("temp_gee_map.html")

    def plot_gdf(self, gdf, highlight_idx=None, auto_zoom=False):
        """
        精简后的渲染逻辑：只做地图跳转和 Marker 显示
        """
        if gdf is None or (hasattr(gdf, 'empty') and gdf.empty):
            return

        # 1. 确定中心点和缩放级别
        if highlight_idx is not None:
            point = gdf.iloc[highlight_idx].geometry
            center = [point.y, point.x]
            zoom = 18 if auto_zoom else 14 # 标注建议缩放到 18 级
        else:
            point = gdf.iloc[0].geometry
            center = [point.y, point.x]
            zoom = 10

        # 2. 创建地图 (直接调用 Google 瓦片，这是最丝滑的方式)
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            zoom_control=False # 如果不需要缩放按钮可以关掉，腾出空间
        )

        # 3. 仅添加标记点
        if highlight_idx is not None:
            folium.Marker(
                location=center,
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)

        # 4. 快速保存并加载
        # 这种方式不涉及 ee 请求，毫秒级响应
        m.save(self.temp_path)
        self.load(QUrl.fromLocalFile(self.temp_path))