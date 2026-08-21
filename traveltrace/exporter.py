"""
导出模块 - 支持交互式HTML、GeoJSON、CSV 三种导出格式
Export module - supports interactive HTML, GeoJSON, and CSV formats.
"""

import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

from .parser import TrackPoint
from .analyzer import TrackAnalyzer, StayPoint, TripSegment


class Exporter:
    """数据导出器 / Data exporter."""

    def __init__(self, points: List[TrackPoint], analyzer: Optional[TrackAnalyzer] = None):
        self.points = points
        self.analyzer = analyzer or TrackAnalyzer(points)

    # ---------- GeoJSON ----------
    def to_geojson(self) -> str:
        """导出为 GeoJSON FeatureCollection（轨迹线 + 停留点）。"""
        features = []

        # 轨迹线
        if len(self.points) >= 2:
            coords = [[p.longitude, p.latitude] for p in self.points]
            features.append({
                "type": "Feature",
                "geometry": {"type": "LineString", "coordinates": coords},
                "properties": {
                    "name": "Travel Path",
                    "point_count": len(self.points),
                },
            })

        # 停留点
        stay_points = self.analyzer.detect_stay_points()
        for sp in stay_points:
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [sp.longitude, sp.latitude]},
                "properties": {
                    "name": "Stay Point",
                    "arrival": sp.arrival_time,
                    "departure": sp.departure_time,
                    "duration_min": round(sp.duration_minutes, 1),
                },
            })

        return json.dumps({
            "type": "FeatureCollection",
            "features": features,
        }, ensure_ascii=False, indent=2)

    # ---------- CSV ----------
    def to_csv(self) -> str:
        """导出为 CSV（轨迹点 + 统计）。"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["timestamp", "latitude", "longitude", "altitude", "accuracy",
                         "velocity", "heading", "source", "activity"])
        for p in self.points:
            writer.writerow([
                p.timestamp, p.latitude, p.longitude,
                p.altitude or "", p.accuracy or "",
                p.velocity or "", p.heading or "",
                p.source, p.activity or "",
            ])
        return output.getvalue()

    def stats_to_csv(self) -> str:
        """导出每日统计为 CSV。"""
        stats = self.analyzer.compute_statistics()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "distance_km", "point_count"])
        for day, info in stats.get("daily", {}).items():
            writer.writerow([day, info["distance_km"], info["points"]])
        return output.getvalue()

    # ---------- 交互式 HTML ----------
    def to_html(self, title: str = "My Travel Trace") -> str:
        """
        导出为单文件交互式 HTML 报告。
        包含：Leaflet 地图、轨迹线、热力图、停留点、统计面板、时间轴。
        所有数据内联，可离线打开（地图瓦片需网络，可切换为离线模式）。
        """
        stats = self.analyzer.compute_statistics()
        stay_points = self.analyzer.detect_stay_points()
        segments = self.analyzer.segment_trips()
        heatmap = self.analyzer.heatmap_data()

        # 准备前端数据
        track_data = [
            [p.latitude, p.longitude, p.timestamp] for p in self.points
        ]
        stay_data = [sp.to_dict() for sp in stay_points]
        segment_data = [s.to_dict() for s in segments]

        # 计算地图中心
        if self.points:
            center_lat = sum(p.latitude for p in self.points) / len(self.points)
            center_lon = sum(p.longitude for p in self.points) / len(self.points)
        else:
            center_lat, center_lon = 30.0, 110.0

        summary = stats.get("summary", {})

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} - TravelTrace</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background:#0f172a; color:#e2e8f0; }}
.header {{ background:linear-gradient(135deg,#1e293b,#334155); padding:20px 30px; border-bottom:2px solid #3b82f6; }}
.header h1 {{ font-size:24px; color:#f8fafc; }}
.header .subtitle {{ color:#94a3b8; margin-top:4px; font-size:14px; }}
.container {{ display:flex; height:calc(100vh - 80px); }}
.sidebar {{ width:340px; background:#1e293b; overflow-y:auto; padding:20px; border-right:1px solid #334155; }}
.map-container {{ flex:1; position:relative; }}
#map {{ width:100%; height:100%; }}
.stat-card {{ background:#0f172a; border-radius:10px; padding:16px; margin-bottom:14px; border:1px solid #334155; }}
.stat-card h3 {{ font-size:13px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:10px; }}
.stat-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.stat-item {{ text-align:center; }}
.stat-value {{ font-size:22px; font-weight:700; color:#3b82f6; }}
.stat-label {{ font-size:11px; color:#64748b; margin-top:2px; }}
.layer-toggle {{ display:flex; gap:8px; margin-bottom:14px; flex-wrap:wrap; }}
.layer-btn {{ padding:8px 14px; border-radius:6px; border:1px solid #475569; background:#0f172a; color:#e2e8f0; cursor:pointer; font-size:12px; transition:all 0.2s; }}
.layer-btn.active {{ background:#3b82f6; border-color:#3b82f6; color:white; }}
.layer-btn:hover {{ border-color:#3b82f6; }}
.timeline {{ max-height:200px; overflow-y:auto; }}
.timeline-item {{ padding:8px 10px; border-left:2px solid #3b82f6; margin-bottom:6px; background:#0f172a; border-radius:0 6px 6px 0; font-size:12px; }}
.timeline-item .time {{ color:#64748b; font-size:11px; }}
.timeline-item .dist {{ color:#22c55e; float:right; }}
.monthly-chart {{ margin-top:10px; }}
.bar-row {{ display:flex; align-items:center; margin-bottom:4px; font-size:11px; }}
.bar-label {{ width:60px; color:#94a3b8; }}
.bar-track {{ flex:1; height:16px; background:#0f172a; border-radius:3px; overflow:hidden; }}
.bar-fill {{ height:100%; background:linear-gradient(90deg,#3b82f6,#8b5cf6); border-radius:3px; }}
.bar-value {{ width:50px; text-align:right; color:#e2e8f0; }}
.leaflet-container {{ background:#0f172a; }}
@media (max-width:768px) {{
    .container {{ flex-direction:column; }}
    .sidebar {{ width:100%; height:40vh; }}
}}
</style>
</head>
<body>
<div class="header">
    <h1>🌍 {title}</h1>
    <div class="subtitle">TravelTrace · 旅行足迹智能可视化引擎 · Generated at {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
</div>
<div class="container">
    <div class="sidebar">
        <div class="stat-card">
            <h3>📊 总览统计</h3>
            <div class="stat-grid">
                <div class="stat-item"><div class="stat-value">{summary.get('total_points',0):,}</div><div class="stat-label">轨迹点</div></div>
                <div class="stat-item"><div class="stat-value">{summary.get('total_distance_km',0):,}</div><div class="stat-label">总公里数</div></div>
                <div class="stat-item"><div class="stat-value">{summary.get('active_days',0)}</div><div class="stat-label">活跃天数</div></div>
                <div class="stat-item"><div class="stat-value">{summary.get('stay_points_count',0)}</div><div class="stat-label">停留点</div></div>
            </div>
        </div>

        <div class="stat-card">
            <h3>🗺️ 图层控制</h3>
            <div class="layer-toggle">
                <button class="layer-btn active" onclick="toggleLayer('track')">轨迹线</button>
                <button class="layer-btn active" onclick="toggleLayer('heat')">热力图</button>
                <button class="layer-btn" onclick="toggleLayer('stay')">停留点</button>
                <button class="layer-btn" onclick="toggleLayer('segments')">行程段</button>
            </div>
        </div>

        <div class="stat-card">
            <h3>📅 月度出行</h3>
            <div class="monthly-chart" id="monthlyChart"></div>
        </div>

        <div class="stat-card">
            <h3>📍 最近行程</h3>
            <div class="timeline" id="timeline"></div>
        </div>
    </div>
    <div class="map-container">
        <div id="map"></div>
    </div>
</div>

<script>
const TRACK_DATA = {json.dumps(track_data)};
const STAY_DATA = {json.dumps(stay_data)};
const SEGMENT_DATA = {json.dumps(segment_data)};
const HEATMAP_DATA = {json.dumps(heatmap)};
const MONTHLY_DATA = {json.dumps(stats.get('monthly', {}))};
const CENTER = [{center_lat:.4f}, {center_lon:.4f}];

// 初始化地图
const map = L.map('map').setView(CENTER, 4);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution: '&copy; OpenStreetMap', maxZoom: 19
}}).addTo(map);

// 轨迹线
const trackLayer = L.layerGroup();
if (TRACK_DATA.length >= 2) {{
    const latlngs = TRACK_DATA.map(p => [p[0], p[1]]);
    L.polyline(latlngs, {{color:'#3b82f6', weight:3, opacity:0.8}}).addTo(trackLayer);
}}
trackLayer.addTo(map);

// 热力图
const heatLayer = L.layerGroup();
if (HEATMAP_DATA.length > 0) {{
    L.heatLayer(HEATMAP_DATA.map(h => [h.lat, h.lng, h.intensity]), {{
        radius: 20, blur: 15, maxZoom: 12, gradient: {{0.2:'blue',0.4:'cyan',0.6:'yellow',0.8:'orange',1.0:'red'}}
    }}).addTo(heatLayer);
}}
heatLayer.addTo(map);

// 停留点
const stayLayer = L.layerGroup();
STAY_DATA.forEach(sp => {{
    const marker = L.circleMarker([sp.latitude, sp.longitude], {{
        radius: Math.min(15, 5 + Math.sqrt(sp.duration_minutes) / 2),
        fillColor: '#f59e0b', color: '#fbbf24', weight: 2, fillOpacity: 0.7
    }}).bindPopup(`<b>停留点</b><br>到达: ${{sp.arrival_time}}<br>离开: ${{sp.departure_time}}<br>时长: ${{sp.duration_minutes}} 分钟`);
    stayLayer.addLayer(marker);
}});

// 行程段
const segmentLayer = L.layerGroup();
const colors = ['#ef4444','#f97316','#eab308','#22c55e','#06b6d4','#8b5cf6','#ec4899'];
SEGMENT_DATA.forEach((seg, i) => {{
    L.polyline([seg.start, seg.end], {{
        color: colors[i % colors.length], weight: 4, opacity: 0.9, dashArray: '8,4'
    }}).bindPopup(`<b>行程段</b><br>距离: ${{seg.distance_km}} km<br>时长: ${{seg.duration_minutes}} 分钟`).addTo(segmentLayer);
}});

// 图层切换
const layers = {{track: trackLayer, heat: heatLayer, stay: stayLayer, segments: segmentLayer}};
function toggleLayer(name) {{
    const btn = event.target;
    const layer = layers[name];
    if (map.hasLayer(layer)) {{ map.removeLayer(layer); btn.classList.remove('active'); }}
    else {{ layer.addTo(map); btn.classList.add('active'); }}
}}

// 月度图表
const monthlyEl = document.getElementById('monthlyChart');
const monthlyEntries = Object.entries(MONTHLY_DATA).sort();
const maxDist = Math.max(...monthlyEntries.map(([_,v]) => v.distance_km), 1);
monthlyEntries.forEach(([month, v]) => {{
    const pct = (v.distance_km / maxDist * 100).toFixed(0);
    monthlyEl.innerHTML += `<div class="bar-row"><span class="bar-label">${{month}}</span><div class="bar-track"><div class="bar-fill" style="width:${{pct}}%"></div></div><span class="bar-value">${{v.distance_km}}km</span></div>`;
}});

// 时间轴
const timelineEl = document.getElementById('timeline');
SEGMENT_DATA.slice(-15).reverse().forEach(seg => {{
    const date = seg.start_time.split('T')[0];
    timelineEl.innerHTML += `<div class="timeline-item"><span class="time">${{date}}</span><span class="dist">${{seg.distance_km}} km</span><br>${{seg.duration_minutes}} 分钟 · ${{seg.point_count}} 点</div>`;
}});

// 自适应边界
if (TRACK_DATA.length > 0) {{
    const bounds = L.latLngBounds(TRACK_DATA.map(p => [p[0], p[1]]));
    map.fitBounds(bounds, {{padding: [50, 50]}});
}}
</script>
</body>
</html>"""
        return html_content

    # ---------- 文件保存 ----------
    def save_html(self, filepath: str, title: str = "My Travel Trace") -> str:
        Path(filepath).write_text(self.to_html(title), encoding="utf-8")
        return filepath

    def save_geojson(self, filepath: str) -> str:
        Path(filepath).write_text(self.to_geojson(), encoding="utf-8")
        return filepath

    def save_csv(self, filepath: str) -> str:
        Path(filepath).write_text(self.to_csv(), encoding="utf-8")
        return filepath
