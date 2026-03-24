

# GeoLabeler

[](https://www.python.org/downloads/)
[](https://www.google.com/search?q=LICENSE)
[](https://www.riverbankcomputing.com/software/pyqt/)

**GeoLabeler** 是一个专为遥感地学样本标注设计的高性能桌面应用。它能够流畅处理 **60,000+** 级别的全球矢量点位数据，并同步从 **Google Earth Engine (GEE)** 实时提取时间序列 NDVI 数据进行可视化标注。


## 📂 项目结构

```text
GeoLabeler/
├── app/                # 源代码
│   ├── core/           # GEE 提取、Vector I/O 逻辑
│   └── gui/            # MainWindow, FastGeomModel, UI 组件
├── requirements.txt    # 依赖列表
└── main.py             # 程序入口
```

## 🛠️ 安装指南

### 1\. 克隆仓库

```bash
git clone https://github.com/yourusername/GeoLabeler.git
cd GeoLabeler
```

### 2\. 安装依赖

```bash
pip install -r requirements.txt
```

### 3\. Google Earth Engine 认证

运行前请确保已完成 GEE 环境初始化：

```bash
earthengine authenticate
```

## 🚀 快速上手

运行主程序：

```bash
python main.py
```

1.  点击 **📂 Upload SHP** 加载你的矢量文件（推荐先尝试 `data/sample/` 里的演示数据）。
2.  在右侧日期筛选器中设置时间范围。
3.  点击表格中的任意行，查看地图定位及自动获取的 NDVI 曲线。
4.  **双击单元格** 即可修改标签，最后点击 **💾 Save** 覆盖保存。

## ⚙️ 性能配置

本项目针对大数据量进行了专项优化：

  - **表格渲染**：仅在视口内加载数据，内存占用极低。
  - **地图抽样**：当点数超过 3000 时，地图会自动开启抽样预览模式，避免渲染卡死。

