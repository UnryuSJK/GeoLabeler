def ensure_wgs84(gdf):
    """确保 GeoDataFrame 转换为 WGS84 坐标系 (EPSG:4326)"""
    if gdf.crs is not None and gdf.crs != "EPSG:4326":
        return gdf.to_crs("EPSG:4326")
    return gdf