import geopandas as gpd
import pandas as pd
import os


class VectorDataManager:
    def __init__(self):
        self.gdf = None
        self.file_path = None
        self.label_column = "u_label"  # 统一的标注字段名

    def load_shapefile(self, path):
        """加载SHP文件并初始化标注列"""
        if not os.path.exists(path):
            raise FileNotFoundError(f"Could not find file: {path}")

        self.file_path = path
        self.gdf = gpd.read_file(path)

        # 核心逻辑：如果SHP里没有标注列，自动创建一个初始值为"未标注"的列
        if self.label_column not in self.gdf.columns:
            self.gdf[self.label_column] = "Unlabeled"

        return self.gdf

    def update_label(self, index, label_value):
        """更新指定索引点的标签"""
        if self.gdf is not None and index in self.gdf.index:
            self.gdf.at[index, self.label_column] = label_value
            return True
        return False

    def get_point_coords(self, index):
        """获取某个点的经纬度 (用于后续API调用)"""
        if self.gdf is not None and index in self.gdf.index:
            point = self.gdf.iloc[index].geometry
            # 假设是经纬度坐标系(WGS84)，返回 x(lon), y(lat)
            return point.x, point.y
        return None

    def save_data(self, output_path=None):
        """保存数据到磁盘"""
        if self.gdf is None:
            return False

        save_path = output_path if output_path else self.file_path
        self.gdf.to_file(save_path)
        return True

    def get_statistics(self):
        """获取当前的标注进度统计"""
        if self.gdf is None:
            return {}
        stats = self.gdf[self.label_column].value_counts().to_dict()
        total = len(self.gdf)
        return {"stats": stats, "total": total}