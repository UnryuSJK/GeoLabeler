import ee
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal
from datetime import datetime, timedelta


class NDVIFetcher(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, lon, lat, start_date, end_date):
        super().__init__()
        self.lon = lon
        self.lat = lat
        # 将字符串转为日期对象进行运算
        self.target_start = datetime.strptime(start_date, "%Y-%m-%d")
        self.target_end = datetime.strptime(end_date, "%Y-%m-%d")

    def run(self):
        try:
            # 1. 计算延伸日期，并强制格式化为 GEE 认的 YYYY-MM-DD
            ext_start_dt = self.target_start - timedelta(days=30)
            ext_end_dt = self.target_end + timedelta(days=30)

            # 边界保护
            s2_launch = datetime(2015, 6, 23)
            if ext_start_dt < s2_launch: ext_start_dt = s2_launch
            if ext_end_dt > datetime.now(): ext_end_dt = datetime.now()

            # 【核心修复】：显式格式化为纯日期字符串
            start_str = ext_start_dt.strftime('%Y-%m-%d')
            end_str = ext_end_dt.strftime('%Y-%m-%d')

            point = ee.Geometry.Point([self.lon, self.lat])

            # 指标计算函数
            def add_indices(img):
                ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                ndwi = img.normalizedDifference(['B3', 'B8']).rename('NDWI')
                mndwi = img.normalizedDifference(['B3', 'B11']).rename('MNDWI')
                lswi = img.normalizedDifference(['B8', 'B11']).rename('LSWI')
                return img.addBands([ndvi, ndwi, mndwi, lswi])

            # 2. 获取数据
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                          .filterBounds(point)
                          .filterDate(start_str, end_str)  # 使用格式化后的字符串
                          .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
                          .map(add_indices))

            def extract_val(img):
                # 显式指定 YYYY-MM-DD 并在 GEE 端截断，确保万无一失
                d_str = img.date().format('YYYY-MM-DD').slice(0, 10)
                stats = img.reduceRegion(ee.Reducer.mean(), point, 10)
                return ee.Feature(None, {
                    'date': d_str,
                    'NDVI': stats.get('NDVI'),
                    'NDWI': stats.get('NDWI'),
                    'MNDWI': stats.get('MNDWI'),
                    'LSWI': stats.get('LSWI')
                })

            features = collection.map(extract_val).getInfo()['features']
            data = [f['properties'] for f in features if f['properties'].get('NDVI') is not None]

            if not data:
                self.error.emit("No imagery found in the expanded range.")
                return

            # ... 前面 GEE 获取 features 和 data 的逻辑保持不变 ...
            df = pd.DataFrame(data)

            # 1. 解析日期并转换格式 (按照你给的逻辑，必须先处理日期)
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            df = df.dropna(subset=['date'])

            # 2. 处理“同一天多景影像” (对应 JS 中的 mosaic 逻辑)
            # 取均值是本地模拟 mosaic 最稳健的方法
            numeric_cols = ['NDVI', 'NDWI', 'MNDWI', 'LSWI']
            df_observed = df.groupby('date')[numeric_cols].mean().sort_index()

            if not df_observed.empty:
                # 3. 生成 5 天步长的空序列 (对应 JS 的 initCol / daysToInterpolate)
                t_start = pd.to_datetime(self.target_start).normalize()
                t_end = pd.to_datetime(self.target_end).normalize()
                target_index = pd.date_range(start=t_start, end=t_end, freq='5D')

                # 4. 执行线性时间插值 (等同于 JS 第 5 步的 timeRatio 计算)
                # reindex 创造坑位 -> union 合并时间轴 -> interpolate 线性填坑
                full_index = df_observed.index.union(target_index).sort_values()
                # limit_direction='both' 对应 JS 中处理边界的情况
                df_interp = df_observed.reindex(full_index).interpolate(method='linear', limit_direction='both')

                # 5. 按照你的 JS 返回逻辑：只提取 target_index 上的插值结果
                df_interp_final = df_interp.loc[target_index].reset_index().rename(columns={'index': 'date'})

                # 6. 按照可视化需求：保留原始观测点数据
                mask_raw = (df_observed.index >= t_start) & (df_observed.index <= t_end)
                df_raw_final = df_observed.loc[mask_raw].reset_index()

                # 发送数据
                self.finished.emit({"raw": df_raw_final, "interp": df_interp_final})
            else:
                self.error.emit("No Sentinel-2 imagery available for this period.")

        except Exception as e:
            # 这里的报错会显示在你的界面中央
            self.error.emit(f"Pipeline Error: {str(e)}")

    def extract_val_func(self, point):
        def extract(img):
            date_str = img.date().format('YYYY-MM-DD').slice(0, 10)
            stats = img.reduceRegion(ee.Reducer.mean(), point, 10)
            return ee.Feature(None, {
                'date': date_str,
                'NDVI': stats.get('NDVI'), 'NDWI': stats.get('NDWI'),
                'MNDWI': stats.get('MNDWI'), 'LSWI': stats.get('LSWI')
            })

        return extract