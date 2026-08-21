"""
内置 Web 可视化服务器 - 零依赖，基于 Python http.server
Built-in web visualization server - zero dependency, based on http.server.
"""

import json
import os
import sys
import cgi
import io
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import List, Optional

from ..parser import LocationParser, TrackPoint
from ..analyzer import TrackAnalyzer
from ..exporter import Exporter


# 全局数据存储（单用户本地工具，不考虑并发）
_global_points: List[TrackPoint] = []


class TravelTraceHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器。"""

    def log_message(self, format, *args):
        """静默日志，只打印关键信息。"""
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/" or path == "/index.html":
            self._serve_index()
        elif path == "/api/stats":
            self._api_stats(params)
        elif path == "/api/track":
            self._api_track(params)
        elif path == "/api/stays":
            self._api_stays(params)
        elif path == "/api/heatmap":
            self._api_heatmap(params)
        elif path == "/api/segments":
            self._api_segments(params)
        elif path == "/api/export":
            self._api_export(params)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/upload":
            self._api_upload()
        else:
            self.send_error(404, "Not Found")

    def _serve_index(self):
        """提供上传+可视化主页面。"""
        html = self._build_upload_page()
        self._send_html(html)

    def _build_upload_page(self) -> str:
        has_data = len(_global_points) > 0
        points_count = len(_global_points)
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TravelTrace - 旅行足迹可视化</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0f172a;color:#e2e8f0}}
.header{{background:linear-gradient(135deg,#1e293b,#334155);padding:16px 24px;border-bottom:2px solid #3b82f6;display:flex;justify-content:space-between;align-items:center}}
.header h1{{font-size:20px;color:#f8fafc}}
.header .status{{font-size:13px;color:#94a3b8}}
.container{{display:flex;height:calc(100vh - 60px)}}
.sidebar{{width:320px;background:#1e293b;overflow-y:auto;padding:16px;border-right:1px solid #334155}}
.map-wrap{{flex:1;position:relative}}
#map{{width:100%;height:100%}}
.upload-area{{border:2px dashed #475569;border-radius:10px;padding:30px;text-align:center;cursor:pointer;transition:all .2s;margin-bottom:16px}}
.upload-area:hover{{border-color:#3b82f6;background:#0f172a}}
.upload-area.dragover{{border-color:#22c55e;background:#0f172a}}
.upload-area .icon{{font-size:36px;margin-bottom:8px}}
.upload-area .text{{font-size:14px;color:#94a3b8}}
.upload-area .hint{{font-size:11px;color:#64748b;margin-top:6px}}
.stat-card{{background:#0f172a;border-radius:10px;padding:14px;margin-bottom:12px;border:1px solid #334155}}
.stat-card h3{{font-size:12px;color:#94a3b8;text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px}}
.stat-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.stat-item{{text-align:center}}
.stat-value{{font-size:20px;font-weight:700;color:#3b82f6}}
.stat-label{{font-size:10px;color:#64748b;margin-top:2px}}
.layer-toggle{{display:flex;gap:6px;flex-wrap:wrap}}
.layer-btn{{padding:6px 12px;border-radius:6px;border:1px solid #475569;background:#0f172a;color:#e2e8f0;cursor:pointer;font-size:11px;transition:all .2s}}
.layer-btn.active{{background:#3b82f6;border-color:#3b82f6;color:#fff}}
.year-select{{width:100%;padding:8px;border-radius:6px;background:#0f172a;color:#e2e8f0;border:1px solid #475569;margin-bottom:12px}}
.monthly .bar-row{{display:flex;align-items:center;margin-bottom:3px;font-size:10px}}
.monthly .bar-label{{width:55px;color:#94a3b8}}
.monthly .bar-track{{flex:1;height:12px;background:#0f172a;border-radius:2px;overflow:hidden}}
.monthly .bar-fill{{height:100%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:2px}}
.monthly .bar-value{{width:45px;text-align:right;color:#e2e8f0}}
.leaflet-container{{background:#0f172a}}
.loading{{display:none;text-align:center;padding:20px;color:#3b82f6}}
</style>
</head>
<body>
<div class="header">
    <h1>🌍 TravelTrace · 旅行足迹可视化</h1>
    <div class="status" id="status">{"✅ 已加载 " + str(points_count) + " 个轨迹点" if has_data else "📂 请上传位置数据"}</div>
</div>
<div class="container">
    <div class="sidebar">
        <div class="upload-area" id="uploadArea">
            <div class="icon">📁</div>
            <div class="text">点击或拖拽上传位置数据</div>
            <div class="hint">支持 Google Location History JSON / GPX / 目录</div>
            <input type="file" id="fileInput" style="display:none" multiple>
        </div>
        <div class="loading" id="loading">⏳ 解析中...</div>

        <div id="statsPanel" style="display:{'block' if has_data else 'none'}">
            <div class="stat-card">
                <h3>📊 总览</h3>
                <div class="stat-grid" id="statsGrid"></div>
            </div>
            <div class="stat-card">
                <h3>🗺️ 图层</h3>
                <div class="layer-toggle">
                    <button class="layer-btn active" onclick="toggleLayer('track')">轨迹</button>
                    <button class="layer-btn active" onclick="toggleLayer('heat')">热力</button>
                    <button class="layer-btn" onclick="toggleLayer('stay')">停留</button>
                </div>
            </div>
            <div class="stat-card">
                <h3>📅 月度出行</h3>
                <div class="monthly" id="monthlyChart"></div>
            </div>
        </div>
    </div>
    <div class="map-wrap"><div id="map"></div></div>
</div>

<script>
let map, trackLayer, heatLayer, stayLayer;
let currentData = {{}};

map = L.map('map').setView([30, 110], 3);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'&copy; OpenStreetMap',maxZoom:19}}).addTo(map);
trackLayer = L.layerGroup().addTo(map);
heatLayer = L.layerGroup().addTo(map);
stayLayer = L.layerGroup();

const layers = {{track:trackLayer,heat:heatLayer,stay:stayLayer}};
function toggleLayer(name){{
    const btn=event.target;const layer=layers[name];
    if(map.hasLayer(layer)){{map.removeLayer(layer);btn.classList.remove('active')}}
    else{{layer.addTo(map);btn.classList.add('active')}}
}}

// 上传
const uploadArea=document.getElementById('uploadArea');
const fileInput=document.getElementById('fileInput');
uploadArea.onclick=()=>fileInput.click();
uploadArea.ondragover=e=>{{e.preventDefault();uploadArea.classList.add('dragover')}};
uploadArea.ondragleave=()=>uploadArea.classList.remove('dragover');
uploadArea.ondrop=e=>{{e.preventDefault();uploadArea.classList.remove('dragover');handleFiles(e.dataTransfer.files)}};
fileInput.onchange=()=>handleFiles(fileInput.files);

async function handleFiles(files){{
    if(!files.length)return;
    document.getElementById('loading').style.display='block';
    const fd=new FormData();
    for(const f of files)fd.append('files',f);
    try{{
        const res=await fetch('/api/upload',{{method:'POST',body:fd}});
        const data=await res.json();
        if(data.success){{
            document.getElementById('status').textContent='✅ 已加载 '+data.count+' 个轨迹点';
            loadData();
        }}else{{
            alert('上传失败: '+data.error);
        }}
    }}catch(e){{alert('上传错误: '+e)}}
    document.getElementById('loading').style.display='none';
}}

async function loadData(){{
    const [stats,track,stays,heat]=await Promise.all([
        fetch('/api/stats').then(r=>r.json()),
        fetch('/api/track').then(r=>r.json()),
        fetch('/api/stays').then(r=>r.json()),
        fetch('/api/heatmap').then(r=>r.json())
    ]);
    currentData={{stats,track,stays,heat}};
    renderStats(stats);
    renderTrack(track);
    renderHeat(heat);
    renderStays(stays);
    document.getElementById('statsPanel').style.display='block';
}}

function renderStats(stats){{
    const s=stats.summary||{{}};
    document.getElementById('statsGrid').innerHTML=`
        <div class="stat-item"><div class="stat-value">${{s.total_points||0}}</div><div class="stat-label">轨迹点</div></div>
        <div class="stat-item"><div class="stat-value">${{(s.total_distance_km||0).toLocaleString()}}</div><div class="stat-label">公里</div></div>
        <div class="stat-item"><div class="stat-value">${{s.active_days||0}}</div><div class="stat-label">活跃天</div></div>
        <div class="stat-item"><div class="stat-value">${{s.stay_points_count||0}}</div><div class="stat-label">停留点</div></div>`;
    const monthly=stats.monthly||{{}};
    const entries=Object.entries(monthly).sort();
    const max=Math.max(...entries.map(([_,v])=>v.distance_km),1);
    document.getElementById('monthlyChart').innerHTML=entries.map(([m,v])=>
        `<div class="bar-row"><span class="bar-label">${{m}}</span><div class="bar-track"><div class="bar-fill" style="width:${{(v.distance_km/max*100).toFixed(0)}}%"></div></div><span class="bar-value">${{v.distance_km}}km</span></div>`
    ).join('');
}}

function renderTrack(track){{
    trackLayer.clearLayers();
    if(track.length>=2){{
        L.polyline(track.map(p=>[p[0],p[1]]),{{color:'#3b82f6',weight:3,opacity:.8}}).addTo(trackLayer);
        map.fitBounds(L.latLngBounds(track.map(p=>[p[0],p[1]])),{{padding:[50,50]}});
    }}
}}
function renderHeat(heat){{
    heatLayer.clearLayers();
    if(heat.length){{
        L.heatLayer(heat.map(h=>[h.lat,h.lng,h.intensity]),{{radius:20,blur:15,maxZoom:12,gradient:{{.2:'blue',.4:'cyan',.6:'yellow',.8:'orange',1:'red'}}}}).addTo(heatLayer);
    }}
}}
function renderStays(stays){{
    stayLayer.clearLayers();
    stays.forEach(sp=>{{
        L.circleMarker([sp.latitude,sp.longitude],{{radius:Math.min(15,5+Math.sqrt(sp.duration_minutes)/2),fillColor:'#f59e0b',color:'#fbbf24',weight:2,fillOpacity:.7}})
        .bindPopup(`<b>停留点</b><br>${{sp.arrival_time}} ~ ${{sp.departure_time}}<br>${{sp.duration_minutes}}分钟`).addTo(stayLayer);
    }});
}}

// 页面加载时如果已有数据则自动渲染
if({str(has_data).lower()}){{ loadData(); }}
</script>
</body>
</html>"""

    def _api_stats(self, params):
        if not _global_points:
            self._send_json({"error": "no data"}, 400)
            return
        analyzer = TrackAnalyzer(_global_points)
        if "year" in params:
            analyzer = analyzer.filter_by_year(int(params["year"][0]))
        self._send_json(analyzer.compute_statistics())

    def _api_track(self, params):
        if not _global_points:
            self._send_json([], 200)
            return
        analyzer = TrackAnalyzer(_global_points)
        if "year" in params:
            analyzer = analyzer.filter_by_year(int(params["year"][0]))
        data = [[p.latitude, p.longitude, p.timestamp] for p in analyzer.points]
        self._send_json(data)

    def _api_stays(self, params):
        if not _global_points:
            self._send_json([], 200)
            return
        analyzer = TrackAnalyzer(_global_points)
        if "year" in params:
            analyzer = analyzer.filter_by_year(int(params["year"][0]))
        dist = float(params.get("distance", [100])[0])
        dur = float(params.get("duration", [15])[0])
        stays = analyzer.detect_stay_points(dist, dur)
        self._send_json([s.to_dict() for s in stays])

    def _api_heatmap(self, params):
        if not _global_points:
            self._send_json([], 200)
            return
        analyzer = TrackAnalyzer(_global_points)
        if "year" in params:
            analyzer = analyzer.filter_by_year(int(params["year"][0]))
        self._send_json(analyzer.heatmap_data())

    def _api_segments(self, params):
        if not _global_points:
            self._send_json([], 200)
            return
        analyzer = TrackAnalyzer(_global_points)
        if "year" in params:
            analyzer = analyzer.filter_by_year(int(params["year"][0]))
        segs = analyzer.segment_trips()
        self._send_json([s.to_dict() for s in segs])

    def _api_export(self, params):
        if not _global_points:
            self._send_json({"error": "no data"}, 400)
            return
        fmt = params.get("format", ["html"])[0]
        analyzer = TrackAnalyzer(_global_points)
        exporter = Exporter(_global_points, analyzer)
        if fmt == "html":
            self._send_html(exporter.to_html())
        elif fmt == "geojson":
            self._send_json(json.loads(exporter.to_geojson()))
        elif fmt == "csv":
            body = exporter.to_csv().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=traveltrace.csv")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def _api_upload(self):
        """处理文件上传。"""
        global _global_points
        try:
            ctype = self.headers.get("Content-Type", "")
            if "multipart/form-data" not in ctype:
                self._send_json({"success": False, "error": "需要 multipart/form-data"}, 400)
                return

            # 解析 multipart
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": ctype},
            )

            all_points = []
            temp_dir = tempfile.mkdtemp(prefix="traveltrace_")

            if "files" in form:
                files = form["files"]
                if not isinstance(files, list):
                    files = [files]
                for file_item in files:
                    if file_item.filename:
                        temp_path = os.path.join(temp_dir, file_item.filename)
                        with open(temp_path, "wb") as f:
                            f.write(file_item.file.read())
                        try:
                            pts = LocationParser.parse_file(temp_path)
                            all_points.extend(pts)
                        except Exception as e:
                            print(f"  解析失败 {file_item.filename}: {e}", file=sys.stderr)

            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            if all_points:
                _global_points = sorted(all_points, key=lambda p: p.timestamp)
                self._send_json({"success": True, "count": len(_global_points)})
            else:
                self._send_json({"success": False, "error": "未解析到有效轨迹点"}, 400)
        except Exception as e:
            self._send_json({"success": False, "error": str(e)}, 500)


def start_server(points: Optional[List[TrackPoint]] = None, host: str = "0.0.0.0", port: int = 8000):
    """启动 Web 服务器。"""
    global _global_points
    if points:
        _global_points = points
    server = HTTPServer((host, port), TravelTraceHandler)
    print(f"\n🌍 TravelTrace Web 服务器已启动")
    print(f"   地址: http://{host}:{port}")
    print(f"   本地: http://localhost:{port}")
    if _global_points:
        print(f"   已预加载: {len(_global_points)} 个轨迹点")
    print(f"   按 Ctrl+C 停止\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        server.server_close()
