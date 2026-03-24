import os
import ee
import folium
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl


class GEEMapView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化 GEE (确保你已经登录过)
        try:
            ee.Initialize()
        except Exception as e:
            print(f"GEE 初始化失败，请检查网络或授权: {e}")

    def update_map(self, lon, lat, zoom=15):
        """
        根据经纬度生成 GEE 影像并渲染成 HTML
        """
        # 1. 创建 folium 地图对象
        m = folium.Map(location=[lat, lon], zoom_start=zoom, control_scale=True)

        # 2. 定义 GEE 影像 (例如：Sentinel-2 2023年最新影像)
        s2_collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(ee.Geometry.Point(lon, lat))
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
                         .sort('system:time_start', False))

        img = s2_collection.first()

        # 3. 设置可视化参数 (真彩色组合)
        vis_params = {
            'bands': ['B4', 'B3', 'B2'],
            'min': 0,
            'max': 3000,
            'gamma': 1.4
        }

        # 4. 获取 GEE 瓦片地址并添加到 folium
        map_id_dict = ee.Image(img).getMapId(vis_params)
        folium.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Google Earth Engine',
            name='Sentinel-2 S2',
            overlay=True,
            control=True
        ).add_to(m)

        # 5. 添加一个标记点
        folium.Marker([lat, lon], popup='Current Point').add_to(m)

        # 6. 将地图保存为临时文件并加载到浏览器组件
        map_path = os.path.abspath("temp_map.html")
        m.save(map_path)
        self.load(QUrl.fromLocalFile(map_path))