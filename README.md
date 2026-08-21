<div align="center">

# 🌍 TravelTrace · 旅行足迹智能可视化引擎

**Intelligent Travel Footprint Visualization Engine**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependency](https://img.shields.io/badge/Core-Zero%20Dependency-orange)]()
[![Tests](https://img.shields.io/badge/Tests-20%20passed-brightgreen)]()

**解析位置数据 · 生成交互式地图 · 发现旅行故事**

[简体中文](#-简体中文) · [繁體中文](#-繁體中文) · [English](#-english)

</div>

---

# 🇨🇳 简体中文

## 🎉 项目介绍

**TravelTrace** 是一款**轻量级、隐私优先**的旅行足迹智能可视化工具。只需导入你的位置历史数据，即可一键生成包含**交互式地图、热力图、停留点分析、行程统计**的可视化报告。

### 💡 解决的痛点

- 📱 **数据沉睡**：Google 位置历史记录了你的每一次出行，却难以直观回顾
- 🔒 **隐私担忧**：第三方可视化工具需要上传数据到云端，存在泄露风险
- 📊 **统计缺失**：原生 Timeline 只提供基础浏览，缺乏距离、天数、频次等深度统计
- 🗺️ **格式割裂**：GPX 轨迹、照片 EXIF、Google Takeout 数据格式不统一，无法整合分析

### ✨ 自研差异化亮点

- **零核心依赖**：纯 Python 标准库实现，无需安装任何第三方包即可运行
- **全本地处理**：所有数据解析、分析、可视化均在本地完成，不上传任何服务器
- **多源融合**：同时支持 Google Location History（新旧双格式）、GPX 轨迹文件、照片 EXIF 坐标
- **智能分析**：基于时空聚类算法自动识别停留点、切分行程段、计算真实行程距离
- **双模式输出**：既可以生成单文件 HTML 报告离线分享，也可以启动内置 Web 服务器交互探索

> 🎯 **灵感来源**：受 GitHub Trending 项目 `google-timeline-visualizer` 启发，原项目为 Kotlin 桌面应用，TravelTrace 重新自研为跨平台 Python 引擎 + Web 可视化方案，新增多源数据支持与智能分析能力。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 📂 **多源解析** | 支持 Google Takeout JSON（旧格式 `locations` + 新格式 Semantic `timelineObjects`）、GPX 1.1 轨迹、JPEG 照片 EXIF GPS |
| 🗺️ **交互式地图** | 基于 Leaflet 的可缩放地图，支持轨迹线、热力图、停留点标记多图层叠加 |
| 🔥 **热力图渲染** | 网格化聚合生成到访密度热力图，直观展示高频活动区域 |
| 📍 **停留点识别** | 经典时空聚类算法（Li et al.），自动检测停留位置与时长，可调距离/时间阈值 |
| 🛤️ **行程分段** | 基于时间间隔与距离跳跃自动切分独立行程，统计每段距离与耗时 |
| 📊 **深度统计** | 总里程、活跃天数、月度出行趋势、活动类型分布、经纬度边界框 |
| 🌐 **内置 Web 服务** | 零依赖 HTTP 服务器，支持浏览器拖拽上传、实时可视化、RESTful API |
| 📤 **多格式导出** | 交互式 HTML（可离线打开）、GeoJSON（GIS 兼容）、CSV（电子表格） |
| 🔍 **按年筛选** | 支持指定年份单独分析，生成年度旅行回顾 |
| 🧪 **测试覆盖** | 20 个单元测试覆盖解析、分析、导出全流程 |

---

## 🚀 快速开始

### 📋 环境要求

- **Python**：3.8 或更高版本（推荐 3.10+）
- **操作系统**：Windows / macOS / Linux 全平台兼容
- **网络**：核心功能离线可用；地图瓦片需网络连接（HTML 报告首次加载 Leaflet CDN）

### 📦 安装

```bash
# 方式一：直接克隆使用（零依赖，无需安装）
git clone https://github.com/gitstq/traveltrace.git
cd traveltrace

# 方式二：安装为命令行工具
pip install -e .

# 验证安装
python -m traveltrace --version
```

### ⚡ 一键生成可视化报告

```bash
# 解析 Google 位置历史并生成 HTML 报告
python -m traveltrace visualize -i location_history.json -o my_travel.html

# 仅查看统计信息
python -m traveltrace parse -i location_history.json -v

# 启动 Web 服务器，浏览器拖拽上传数据
python -m traveltrace serve --port 8080
```

### 📥 获取 Google 位置历史数据

1. 访问 [Google Takeout](https://takeout.google.com/)
2. 选择「位置记录 / Location History」
3. 导出格式选择 **JSON**
4. 下载解压后，找到 `Location History.json` 或 `Semantic Location History/` 目录

---

## 📖 详细使用指南

### 🔧 CLI 命令详解

#### 1️⃣ `parse` — 解析与统计

```bash
# 基础统计
python -m traveltrace parse -i location_history.json

# 详细月度统计 + 导出JSON
python -m traveltrace parse -i location_history.json -v -o stats.json

# 解析整个目录（支持混合JSON/GPX/照片）
python -m traveltrace parse -i ./my_takeout_folder/
```

#### 2️⃣ `visualize` — 生成交互式报告

```bash
# 生成报告
python -m traveltrace visualize -i location_history.json -o report.html

# 指定标题和年份
python -m traveltrace visualize -i location_history.json -t "我的2024旅行" --year 2024

# 生成后自动打开浏览器预览
python -m traveltrace visualize -i location_history.json --serve --port 8000
```

#### 3️⃣ `export` — 多格式导出

```bash
# 导出 GeoJSON（可导入 QGIS / Google Earth）
python -m traveltrace export -i track.gpx -f geojson -o track.geojson

# 导出 CSV（原始轨迹点）
python -m traveltrace export -i location_history.json -f csv -o points.csv

# 导出 CSV（每日统计）
python -m traveltrace export -i location_history.json -f csv --stats -o daily.csv

# 导出 HTML 报告
python -m traveltrace export -i location_history.json -f html -t "年度回顾" -o annual.html
```

#### 4️⃣ `stays` — 停留点分析

```bash
# 默认参数（100米范围，停留≥15分钟）
python -m traveltrace stays -i location_history.json

# 自定义阈值
python -m traveltrace stays -i location_history.json --distance 200 --duration 30 -o stays.json
```

#### 5️⃣ `serve` — Web 可视化服务器

```bash
# 启动服务器（空数据，浏览器上传）
python -m traveltrace serve --host 0.0.0.0 --port 8080

# 预加载数据文件
python -m traveltrace serve -i location_history.json --port 8080
```

启动后访问 `http://localhost:8080`，支持：
- 📁 拖拽上传位置数据文件
- 🗺️ 实时地图可视化（轨迹/热力/停留点图层切换）
- 📊 动态统计面板
- 📅 月度出行柱状图

### 🔌 作为 Python 库使用

```python
from traveltrace import LocationParser, TrackAnalyzer, Exporter

# 解析数据
points = LocationParser.parse_file("location_history.json")
print(f"解析到 {len(points)} 个轨迹点")

# 分析
analyzer = TrackAnalyzer(points)
stats = analyzer.compute_statistics()
stays = analyzer.detect_stay_points(distance_threshold_m=150, duration_threshold_min=20)
print(f"总行程: {stats['summary']['total_distance_km']} km")
print(f"停留点: {len(stays)} 个")

# 导出
exporter = Exporter(points, analyzer)
exporter.save_html("my_report.html", title="我的旅行足迹")
exporter.save_geojson("my_track.geojson")
```

### 📁 支持的数据源格式

| 格式 | 文件扩展名 | 说明 |
|------|-----------|------|
| Google Location History（旧） | `.json` | `{"locations": [{timestampMs, latitudeE7, ...}]}` |
| Google Semantic Location History（新） | `.json` | `{"timelineObjects": [{activitySegment, placeVisit}]}` |
| GPX 轨迹 | `.gpx` | 标准 GPS 交换格式，支持 trk / wpt |
| JPEG 照片 | `.jpg` `.jpeg` | 从 EXIF 提取 GPS 坐标与拍摄时间 |

---

## 💡 设计思路与迭代规划

### 🏗️ 技术架构

```
┌─────────────────────────────────────────────┐
│                  用户输入层                    │
│   CLI 命令  │  Web UI  │  Python API         │
├─────────────────────────────────────────────┤
│                  解析层                       │
│   Google JSON │  GPX XML  │  EXIF 二进制      │
├─────────────────────────────────────────────┤
│                  分析层                       │
│   停留点识别 │ 行程分段  │ 统计聚合  │ 热力图  │
├─────────────────────────────────────────────┤
│                  输出层                       │
│   HTML 报告  │  GeoJSON  │  CSV    │ Web API │
└─────────────────────────────────────────────┘
```

### 🤔 技术选型原因

- **纯 Python 标准库**：最大化兼容性，用户无需 `pip install` 即可运行；EXIF 解析自行实现极简 JPEG 解析器，避免强制依赖 Pillow
- **Leaflet.js**：成熟轻量的开源地图库，CDN 加载即可使用，支持热力图插件
- **内置 HTTP 服务器**：基于 `http.server`，零依赖启动，适合本地单用户使用场景
- **时空聚类算法**：采用学术界经典的 Li et al. 停留点检测算法，参数可调，结果可解释

### 🗺️ 后续迭代计划

- [ ] **v1.1**：反向地理编码（本地地名库，无需外部 API）
- [ ] **v1.1**：支持 Strava / Nike Run Club 等运动 APP 数据导入
- [ ] **v1.2**：旅行照片时间轴自动关联（按时间匹配照片与位置）
- [ ] **v1.2**：年度旅行视频生成（轨迹路径动画 + 地图缩放）
- [ ] **v1.3**：多人轨迹叠加对比（情侣/家庭旅行回顾）
- [ ] **v1.3**：离线地图瓦片包支持（完全离线可用）

### 🤝 社区贡献方向

- 新增数据源解析器（如 Apple 健康导出、运动手表数据）
- 前端可视化主题与交互优化
- 性能优化（超大数据集百万级点处理）
- 文档翻译与多语言扩展

---

## 📦 打包与部署指南

### 🐍 作为 Python 包安装

```bash
# 开发模式安装
pip install -e .

# 构建分发包
python -m pip install --upgrade build
python -m build
# 产物在 dist/ 目录
```

### 📄 单文件 HTML 报告部署

生成的 HTML 报告为**完全自包含**（数据内联，仅地图瓦片需网络），可直接：
- 本地双击打开
- 部署到任意静态托管（GitHub Pages / Vercel / Netlify）
- 通过邮件/消息分享给他人

### 🖥️ Web 服务器部署

```bash
# 后台运行（Linux/macOS）
nohup python -m traveltrace serve --host 0.0.0.0 --port 8080 > traveltrace.log 2>&1 &

# 使用 systemd 管理（生产环境建议）
# 参考配置见 docs/ 目录
```

### 🐳 Docker 部署

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8080
CMD ["python", "-m", "traveltrace", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

### ✅ 兼容环境

| 环境 | 版本 | 状态 |
|------|------|------|
| Python | 3.8 / 3.9 / 3.10 / 3.11 / 3.12 | ✅ 完全兼容 |
| Windows | 10 / 11 | ✅ 完全兼容 |
| macOS | 11+ | ✅ 完全兼容 |
| Linux | Ubuntu / Debian / CentOS | ✅ 完全兼容 |
| 浏览器 | Chrome / Firefox / Safari / Edge | ✅ 地图可视化兼容 |

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 🔄 PR 提交规范

1. Fork 本仓库并创建特性分支：`git checkout -b feat/amazing-feature`
2. 提交信息遵循 **Angular 规范**：
   - `feat:` 新增功能
   - `fix:` 修复问题
   - `docs:` 文档更新
   - `refactor:` 代码重构
   - `test:` 测试相关
   - `chore:` 构建/工具链
3. 确保所有测试通过：`python -m pytest tests/`
4. 提交 Pull Request，详细描述改动内容与动机

### 🐛 Issue 反馈规则

- **Bug 报告**：请附上操作系统、Python 版本、复现步骤与错误日志
- **功能请求**：请描述使用场景与期望行为
- **数据格式问题**：请附上脱敏后的样本数据片段

### 📜 行为准则

请在交流中保持尊重与友善，我们致力于打造开放包容的社区。

---

## 📄 开源协议说明

本项目基于 **MIT License** 开源，详见 [LICENSE](LICENSE) 文件。

> MIT 协议允许你自由使用、修改、分发本项目，包括商业用途，只需保留原始版权与许可声明。

---

<br>

# 🇭🇰 繁體中文

## 🎉 專案介紹

**TravelTrace** 是一款**輕量級、隱私優先**的旅行足跡智慧視覺化工具。只需匯入你的位置歷史資料，即可一鍵生成包含**互動式地圖、熱力圖、停留點分析、行程統計**的視覺化報告。

### 💡 解決的痛點

- 📱 **資料沉睡**：Google 位置歷史記錄了你的每一次出行，卻難以直觀回顧
- 🔒 **隱私疑慮**：第三方視覺化工具需要上傳資料到雲端，存在外洩風險
- 📊 **統計不足**：原生 Timeline 只提供基礎瀏覽，缺乏距離、天數、頻次等深度統計
- 🗺️ **格式割裂**：GPX 軌跡、照片 EXIF、Google Takeout 資料格式不統一，無法整合分析

### ✨ 自研差異化亮點

- **零核心依賴**：純 Python 標準函式庫實現，無需安裝任何第三方套件即可運行
- **全本機處理**：所有資料解析、分析、視覺化均在本機完成，不上傳任何伺服器
- **多源融合**：同時支援 Google Location History（新舊雙格式）、GPX 軌跡檔案、照片 EXIF 座標
- **智慧分析**：基於時空叢集演算法自動辨識停留點、切分行程段、計算真實行程距離
- **雙模式輸出**：既可以生成單檔 HTML 報告離線分享，也可以啟動內建 Web 伺服器互動探索

> 🎯 **靈感來源**：受 GitHub Trending 專案 `google-timeline-visualizer` 啟發，原專案為 Kotlin 桌面應用，TravelTrace 重新自研為跨平台 Python 引擎 + Web 視覺化方案，新增多源資料支援與智慧分析能力。

---

## ✨ 核心功能

| 功能 | 說明 |
|------|------|
| 📂 **多源解析** | 支援 Google Takeout JSON（舊格式 `locations` + 新格式 Semantic `timelineObjects`）、GPX 1.1 軌跡、JPEG 照片 EXIF GPS |
| 🗺️ **互動式地圖** | 基於 Leaflet 的可縮放地圖，支援軌跡線、熱力圖、停留點標記多圖層疊加 |
| 🔥 **熱力圖渲染** | 網格化聚合生成到訪密度熱力圖，直觀展示高頻活動區域 |
| 📍 **停留點辨識** | 經典時空叢集演算法（Li et al.），自動偵測停留位置與時長，可調距離/時間閾值 |
| 🛤️ **行程分段** | 基於時間間隔與距離跳躍自動切分獨立行程，統計每段距離與耗時 |
| 📊 **深度統計** | 總里程、活躍天數、月度出行趨勢、活動類型分佈、經緯度邊界框 |
| 🌐 **內建 Web 服務** | 零依賴 HTTP 伺服器，支援瀏覽器拖放上傳、即時視覺化、RESTful API |
| 📤 **多格式匯出** | 互動式 HTML（可離線開啟）、GeoJSON（GIS 相容）、CSV（電子試算表） |
| 🔍 **按年篩選** | 支援指定年份單獨分析，生成年度旅行回顧 |
| 🧪 **測試覆蓋** | 20 個單元測試覆蓋解析、分析、匯出全流程 |

---

## 🚀 快速開始

### 📋 環境需求

- **Python**：3.8 或更高版本（推薦 3.10+）
- **作業系統**：Windows / macOS / Linux 全平台相容
- **網路**：核心功能離線可用；地圖圖塊需網路連線（HTML 報告首次載入 Leaflet CDN）

### 📦 安裝

```bash
# 方式一：直接複製使用（零依賴，無需安裝）
git clone https://github.com/gitstq/traveltrace.git
cd traveltrace

# 方式二：安裝為命令列工具
pip install -e .

# 驗證安裝
python -m traveltrace --version
```

### ⚡ 一鍵生成視覺化報告

```bash
# 解析 Google 位置歷史並生成 HTML 報告
python -m traveltrace visualize -i location_history.json -o my_travel.html

# 僅查看統計資訊
python -m traveltrace parse -i location_history.json -v

# 啟動 Web 伺服器，瀏覽器拖放上傳資料
python -m traveltrace serve --port 8080
```

### 📥 取得 Google 位置歷史資料

1. 前往 [Google Takeout](https://takeout.google.com/)
2. 選取「位置記錄 / Location History」
3. 匯出格式選擇 **JSON**
4. 下載解壓縮後，找到 `Location History.json` 或 `Semantic Location History/` 目錄

---

## 📖 詳細使用指南

### 🔧 CLI 指令詳解

#### 1️⃣ `parse` — 解析與統計

```bash
# 基礎統計
python -m traveltrace parse -i location_history.json

# 詳細月度統計 + 匯出JSON
python -m traveltrace parse -i location_history.json -v -o stats.json

# 解析整個目錄（支援混合JSON/GPX/照片）
python -m traveltrace parse -i ./my_takeout_folder/
```

#### 2️⃣ `visualize` — 生成互動式報告

```bash
# 生成報告
python -m traveltrace visualize -i location_history.json -o report.html

# 指定標題和年份
python -m traveltrace visualize -i location_history.json -t "我的2024旅行" --year 2024

# 生成後自動開啟瀏覽器預覽
python -m traveltrace visualize -i location_history.json --serve --port 8000
```

#### 3️⃣ `export` — 多格式匯出

```bash
# 匯出 GeoJSON（可匯入 QGIS / Google Earth）
python -m traveltrace export -i track.gpx -f geojson -o track.geojson

# 匯出 CSV（原始軌跡點）
python -m traveltrace export -i location_history.json -f csv -o points.csv

# 匯出 CSV（每日統計）
python -m traveltrace export -i location_history.json -f csv --stats -o daily.csv

# 匯出 HTML 報告
python -m traveltrace export -i location_history.json -f html -t "年度回顧" -o annual.html
```

#### 4️⃣ `stays` — 停留點分析

```bash
# 預設參數（100公尺範圍，停留≥15分鐘）
python -m traveltrace stays -i location_history.json

# 自訂閾值
python -m traveltrace stays -i location_history.json --distance 200 --duration 30 -o stays.json
```

#### 5️⃣ `serve` — Web 視覺化伺服器

```bash
# 啟動伺服器（空資料，瀏覽器上傳）
python -m traveltrace serve --host 0.0.0.0 --port 8080

# 預載資料檔案
python -m traveltrace serve -i location_history.json --port 8080
```

啟動後存取 `http://localhost:8080`，支援：
- 📁 拖放上傳位置資料檔案
- 🗺️ 即時地圖視覺化（軌跡/熱力/停留點圖層切換）
- 📊 動態統計面板
- 📅 月度出行長條圖

### 🔌 作為 Python 函式庫使用

```python
from traveltrace import LocationParser, TrackAnalyzer, Exporter

# 解析資料
points = LocationParser.parse_file("location_history.json")
print(f"解析到 {len(points)} 個軌跡點")

# 分析
analyzer = TrackAnalyzer(points)
stats = analyzer.compute_statistics()
stays = analyzer.detect_stay_points(distance_threshold_m=150, duration_threshold_min=20)
print(f"總行程: {stats['summary']['total_distance_km']} km")
print(f"停留點: {len(stays)} 個")

# 匯出
exporter = Exporter(points, analyzer)
exporter.save_html("my_report.html", title="我的旅行足跡")
exporter.save_geojson("my_track.geojson")
```

### 📁 支援的資料源格式

| 格式 | 檔案副檔名 | 說明 |
|------|-----------|------|
| Google Location History（舊） | `.json` | `{"locations": [{timestampMs, latitudeE7, ...}]}` |
| Google Semantic Location History（新） | `.json` | `{"timelineObjects": [{activitySegment, placeVisit}]}` |
| GPX 軌跡 | `.gpx` | 標準 GPS 交換格式，支援 trk / wpt |
| JPEG 照片 | `.jpg` `.jpeg` | 從 EXIF 提取 GPS 座標與拍攝時間 |

---

## 💡 設計思路與迭代規劃

### 🏗️ 技術架構

```
┌─────────────────────────────────────────────┐
│                  使用者輸入層                  │
│   CLI 指令  │  Web UI  │  Python API         │
├─────────────────────────────────────────────┤
│                  解析層                       │
│   Google JSON │  GPX XML  │  EXIF 二進位      │
├─────────────────────────────────────────────┤
│                  分析層                       │
│   停留點辨識 │ 行程分段  │ 統計聚合  │ 熱力圖  │
├─────────────────────────────────────────────┤
│                  輸出層                       │
│   HTML 報告  │  GeoJSON  │  CSV    │ Web API │
└─────────────────────────────────────────────┘
```

### 🤔 技術選型原因

- **純 Python 標準函式庫**：最大化相容性，使用者無需 `pip install` 即可運行；EXIF 解析自行實現極簡 JPEG 解析器，避免強制依賴 Pillow
- **Leaflet.js**：成熟輕量的開源地圖庫，CDN 載入即可使用，支援熱力圖外掛
- **內建 HTTP 伺服器**：基於 `http.server`，零依賴啟動，適合本機單使用者使用場景
- **時空叢集演算法**：採用學術界經典的 Li et al. 停留點偵測演算法，參數可調，結果可解釋

### 🗺️ 後續迭代計畫

- [ ] **v1.1**：反向地理編碼（本機地名庫，無需外部 API）
- [ ] **v1.1**：支援 Strava / Nike Run Club 等運動 APP 資料匯入
- [ ] **v1.2**：旅行照片時間軸自動關聯（按時間匹配照片與位置）
- [ ] **v1.2**：年度旅行影片生成（軌跡路徑動畫 + 地圖縮放）
- [ ] **v1.3**：多人軌跡疊加對比（伴侶/家庭旅行回顧）
- [ ] **v1.3**：離線地圖圖塊包支援（完全離線可用）

### 🤝 社群貢獻方向

- 新增資料源解析器（如 Apple 健康匯出、運動手錶資料）
- 前端視覺化主題與互動優化
- 效能優化（超大型資料集百萬級點處理）
- 文件翻譯與多語言擴展

---

## 📦 打包與部署指南

### 🐍 作為 Python 套件安裝

```bash
# 開發模式安裝
pip install -e .

# 構建分發套件
python -m pip install --upgrade build
python -m build
# 產物在 dist/ 目錄
```

### 📄 單檔 HTML 報告部署

生成的 HTML 報告為**完全自包含**（資料內聯，僅地圖圖塊需網路），可直接：
- 本機雙擊開啟
- 部署到任意靜態託管（GitHub Pages / Vercel / Netlify）
- 透過郵件/訊息分享給他人

### 🖥️ Web 伺服器部署

```bash
# 背景運行（Linux/macOS）
nohup python -m traveltrace serve --host 0.0.0.0 --port 8080 > traveltrace.log 2>&1 &

# 使用 systemd 管理（生產環境建議）
# 參考設定見 docs/ 目錄
```

### 🐳 Docker 部署

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8080
CMD ["python", "-m", "traveltrace", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

### ✅ 相容環境

| 環境 | 版本 | 狀態 |
|------|------|------|
| Python | 3.8 / 3.9 / 3.10 / 3.11 / 3.12 | ✅ 完全相容 |
| Windows | 10 / 11 | ✅ 完全相容 |
| macOS | 11+ | ✅ 完全相容 |
| Linux | Ubuntu / Debian / CentOS | ✅ 完全相容 |
| 瀏覽器 | Chrome / Firefox / Safari / Edge | ✅ 地圖視覺化相容 |

---

## 🤝 貢獻指南

我們歡迎所有形式的貢獻！

### 🔄 PR 提交規範

1. Fork 本倉庫並建立特性分支：`git checkout -b feat/amazing-feature`
2. 提交資訊遵循 **Angular 規範**：
   - `feat:` 新增功能
   - `fix:` 修復問題
   - `docs:` 文件更新
   - `refactor:` 程式碼重構
   - `test:` 測試相關
   - `chore:` 構建/工具鏈
3. 確保所有測試通過：`python -m pytest tests/`
4. 提交 Pull Request，詳細描述改動內容與動機

### 🐛 Issue 回饋規則

- **Bug 報告**：請附上作業系統、Python 版本、重現步驟與錯誤日誌
- **功能請求**：請描述使用場景與期望行為
- **資料格式問題**：請附上脫敏後的樣本資料片段

### 📜 行為準則

請在交流中保持尊重與友善，我們致力於打造開放包容的社群。

---

## 📄 開源協議說明

本專案基於 **MIT License** 開源，詳見 [LICENSE](LICENSE) 檔案。

> MIT 協議允許你自由使用、修改、分發本專案，包括商業用途，只需保留原始版權與許可聲明。

---

<br>

# 🇬🇧 English

## 🎉 Project Introduction

**TravelTrace** is a **lightweight, privacy-first** intelligent travel footprint visualization tool. Simply import your location history data and generate a visualization report featuring an **interactive map, heatmap, stay point analysis, and trip statistics** in one click.

### 💡 Problems Solved

- 📱 **Dormant Data**: Google Location History records every trip you take, yet it's hard to review intuitively
- 🔒 **Privacy Concerns**: Third-party visualization tools require uploading data to the cloud, risking exposure
- 📊 **Missing Statistics**: Native Timeline only offers basic browsing, lacking deep insights like distance, days, and frequency
- 🗺️ **Fragmented Formats**: GPX tracks, photo EXIF, and Google Takeout data use incompatible formats and can't be analyzed together

### ✨ Self-Developed Differentiation Highlights

- **Zero Core Dependencies**: Pure Python standard library implementation — runs without installing any third-party packages
- **Fully Local Processing**: All parsing, analysis, and visualization happen locally — nothing is uploaded to any server
- **Multi-Source Fusion**: Supports Google Location History (both old and new formats), GPX track files, and photo EXIF coordinates simultaneously
- **Intelligent Analysis**: Automatically detects stay points, segments trips, and calculates real travel distance using spatiotemporal clustering
- **Dual Output Modes**: Generate a single-file HTML report for offline sharing, or launch the built-in web server for interactive exploration

> 🎯 **Inspiration**: Inspired by the GitHub Trending project `google-timeline-visualizer` (a Kotlin desktop app), TravelTrace was re-engineered from scratch as a cross-platform Python engine + Web visualization solution, adding multi-source data support and intelligent analysis capabilities.

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 📂 **Multi-Source Parsing** | Google Takeout JSON (old `locations` + new Semantic `timelineObjects`), GPX 1.1 tracks, JPEG photo EXIF GPS |
| 🗺️ **Interactive Map** | Leaflet-based zoomable map with track line, heatmap, and stay point marker layers |
| 🔥 **Heatmap Rendering** | Grid-based aggregation generates visit-density heatmaps to visualize high-activity areas |
| 📍 **Stay Point Detection** | Classic spatiotemporal clustering (Li et al.) — auto-detects stay locations and duration, with adjustable distance/time thresholds |
| 🛤️ **Trip Segmentation** | Automatically splits independent trips based on time gaps and distance jumps, with per-segment distance and duration stats |
| 📊 **Deep Statistics** | Total mileage, active days, monthly travel trends, activity type distribution, bounding box |
| 🌐 **Built-in Web Server** | Zero-dependency HTTP server with browser drag-and-drop upload, real-time visualization, and RESTful API |
| 📤 **Multi-Format Export** | Interactive HTML (offline-ready), GeoJSON (GIS-compatible), CSV (spreadsheet) |
| 🔍 **Year Filtering** | Analyze a specific year independently for annual travel reviews |
| 🧪 **Test Coverage** | 20 unit tests covering parsing, analysis, and export workflows |

---

## 🚀 Quick Start

### 📋 Requirements

- **Python**: 3.8 or higher (3.10+ recommended)
- **OS**: Windows / macOS / Linux — fully cross-platform
- **Network**: Core features work offline; map tiles require internet (HTML report loads Leaflet CDN on first open)

### 📦 Installation

```bash
# Option 1: Clone and use directly (zero dependency, no install needed)
git clone https://github.com/gitstq/traveltrace.git
cd traveltrace

# Option 2: Install as a CLI tool
pip install -e .

# Verify
python -m traveltrace --version
```

### ⚡ One-Click Visualization Report

```bash
# Parse Google Location History and generate HTML report
python -m traveltrace visualize -i location_history.json -o my_travel.html

# View statistics only
python -m traveltrace parse -i location_history.json -v

# Start web server and drag-and-drop data in browser
python -m traveltrace serve --port 8080
```

### 📥 Getting Google Location History Data

1. Visit [Google Takeout](https://takeout.google.com/)
2. Select "Location History"
3. Choose **JSON** as the export format
4. Download and extract — find `Location History.json` or the `Semantic Location History/` directory

---

## 📖 Detailed Usage Guide

### 🔧 CLI Command Reference

#### 1️⃣ `parse` — Parse & Statistics

```bash
# Basic statistics
python -m traveltrace parse -i location_history.json

# Verbose monthly stats + export JSON
python -m traveltrace parse -i location_history.json -v -o stats.json

# Parse an entire directory (mixed JSON/GPX/photos supported)
python -m traveltrace parse -i ./my_takeout_folder/
```

#### 2️⃣ `visualize` — Generate Interactive Report

```bash
# Generate report
python -m traveltrace visualize -i location_history.json -o report.html

# Custom title and year filter
python -m traveltrace visualize -i location_history.json -t "My 2024 Travels" --year 2024

# Auto-open browser preview after generation
python -m traveltrace visualize -i location_history.json --serve --port 8000
```

#### 3️⃣ `export` — Multi-Format Export

```bash
# Export GeoJSON (import into QGIS / Google Earth)
python -m traveltrace export -i track.gpx -f geojson -o track.geojson

# Export CSV (raw track points)
python -m traveltrace export -i location_history.json -f csv -o points.csv

# Export CSV (daily statistics)
python -m traveltrace export -i location_history.json -f csv --stats -o daily.csv

# Export HTML report
python -m traveltrace export -i location_history.json -f html -t "Annual Review" -o annual.html
```

#### 4️⃣ `stays` — Stay Point Analysis

```bash
# Default parameters (100m radius, ≥15 min stay)
python -m traveltrace stays -i location_history.json

# Custom thresholds
python -m traveltrace stays -i location_history.json --distance 200 --duration 30 -o stays.json
```

#### 5️⃣ `serve` — Web Visualization Server

```bash
# Start server (empty data, upload in browser)
python -m traveltrace serve --host 0.0.0.0 --port 8080

# Pre-load a data file
python -m traveltrace serve -i location_history.json --port 8080
```

After starting, visit `http://localhost:8080` for:
- 📁 Drag-and-drop location data file upload
- 🗺️ Real-time map visualization (track/heatmap/stay layer toggling)
- 📊 Dynamic statistics panel
- 📅 Monthly travel bar chart

### 🔌 Using as a Python Library

```python
from traveltrace import LocationParser, TrackAnalyzer, Exporter

# Parse data
points = LocationParser.parse_file("location_history.json")
print(f"Parsed {len(points)} track points")

# Analyze
analyzer = TrackAnalyzer(points)
stats = analyzer.compute_statistics()
stays = analyzer.detect_stay_points(distance_threshold_m=150, duration_threshold_min=20)
print(f"Total distance: {stats['summary']['total_distance_km']} km")
print(f"Stay points: {len(stays)}")

# Export
exporter = Exporter(points, analyzer)
exporter.save_html("my_report.html", title="My Travel Footprint")
exporter.save_geojson("my_track.geojson")
```

### 📁 Supported Data Source Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| Google Location History (old) | `.json` | `{"locations": [{timestampMs, latitudeE7, ...}]}` |
| Google Semantic Location History (new) | `.json` | `{"timelineObjects": [{activitySegment, placeVisit}]}` |
| GPX Track | `.gpx` | Standard GPS exchange format, supports trk / wpt |
| JPEG Photo | `.jpg` `.jpeg` | Extracts GPS coordinates and capture time from EXIF |

---

## 💡 Design Philosophy & Roadmap

### 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│               Input Layer                     │
│   CLI Commands  │  Web UI  │  Python API      │
├─────────────────────────────────────────────┤
│               Parsing Layer                   │
│   Google JSON  │  GPX XML  │  EXIF Binary     │
├─────────────────────────────────────────────┤
│               Analysis Layer                  │
│   Stay Detection │ Trip Segmentation │ Stats  │
│              Heatmap Aggregation              │
├─────────────────────────────────────────────┤
│               Output Layer                    │
│   HTML Report  │  GeoJSON  │  CSV  │ Web API  │
└─────────────────────────────────────────────┘
```

### 🤔 Technology Choices

- **Pure Python Standard Library**: Maximizes compatibility — users can run without `pip install`; EXIF parsing uses a custom minimal JPEG parser to avoid forcing a Pillow dependency
- **Leaflet.js**: Mature, lightweight open-source mapping library, works via CDN with heatmap plugin support
- **Built-in HTTP Server**: Based on `http.server`, zero-dependency startup, ideal for local single-user scenarios
- **Spatiotemporal Clustering**: Uses the academically classic Li et al. stay point detection algorithm — tunable parameters, interpretable results

### 🗺️ Roadmap

- [ ] **v1.1**: Reverse geocoding (local place-name database, no external API needed)
- [ ] **v1.1**: Support for Strava / Nike Run Club and other fitness app data imports
- [ ] **v1.2**: Auto-link travel photos to timeline (match photos to locations by timestamp)
- [ ] **v1.2**: Annual travel video generation (track path animation + map zoom)
- [ ] **v1.3**: Multi-person track overlay comparison (couple/family travel reviews)
- [ ] **v1.3**: Offline map tile bundle support (fully offline capability)

### 🤝 Community Contribution Areas

- New data source parsers (e.g., Apple Health export, sports watch data)
- Frontend visualization themes and interaction improvements
- Performance optimization (million-point dataset processing)
- Documentation translation and multi-language expansion

---

## 📦 Packaging & Deployment Guide

### 🐍 Install as a Python Package

```bash
# Development mode install
pip install -e .

# Build distribution
python -m pip install --upgrade build
python -m build
# Artifacts in dist/ directory
```

### 📄 Single-File HTML Report Deployment

Generated HTML reports are **fully self-contained** (data inlined, only map tiles need network). You can:
- Open locally by double-clicking
- Deploy to any static host (GitHub Pages / Vercel / Netlify)
- Share via email or messaging

### 🖥️ Web Server Deployment

```bash
# Run in background (Linux/macOS)
nohup python -m traveltrace serve --host 0.0.0.0 --port 8080 > traveltrace.log 2>&1 &

# Use systemd for production management
# See docs/ directory for reference config
```

### 🐳 Docker Deployment

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8080
CMD ["python", "-m", "traveltrace", "serve", "--host", "0.0.0.0", "--port", "8080"]
```

### ✅ Compatibility Matrix

| Environment | Version | Status |
|-------------|---------|--------|
| Python | 3.8 / 3.9 / 3.10 / 3.11 / 3.12 | ✅ Fully compatible |
| Windows | 10 / 11 | ✅ Fully compatible |
| macOS | 11+ | ✅ Fully compatible |
| Linux | Ubuntu / Debian / CentOS | ✅ Fully compatible |
| Browser | Chrome / Firefox / Safari / Edge | ✅ Map visualization compatible |

---

## 🤝 Contributing

We welcome all forms of contribution!

### 🔄 PR Guidelines

1. Fork this repository and create a feature branch: `git checkout -b feat/amazing-feature`
2. Commit messages follow **Angular Conventions**:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation update
   - `refactor:` Code refactoring
   - `test:` Test-related
   - `chore:` Build / tooling
3. Ensure all tests pass: `python -m pytest tests/`
4. Submit a Pull Request with a detailed description of changes and motivation

### 🐛 Issue Guidelines

- **Bug Reports**: Include OS, Python version, reproduction steps, and error logs
- **Feature Requests**: Describe the use case and expected behavior
- **Data Format Issues**: Include sanitized sample data snippets

### 📜 Code of Conduct

Please be respectful and kind in all interactions. We are committed to building an open and inclusive community.

---

## 📄 License

This project is open-sourced under the **MIT License**. See the [LICENSE](LICENSE) file for details.

> The MIT License allows you to freely use, modify, and distribute this project, including for commercial purposes, as long as you retain the original copyright and license notice.

---

<div align="center">

**Made with 🌍 by TravelTrace Contributors**

[⬆ Back to Top](#-traveltrace--旅行足迹智能可视化引擎)

</div>
