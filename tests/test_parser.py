"""
TravelTrace 单元测试 / Unit tests for TravelTrace.
"""

import json
import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta

from traveltrace.parser import LocationParser, TrackPoint
from traveltrace.analyzer import TrackAnalyzer, StayPoint, TripSegment
from traveltrace.exporter import Exporter


# ---------- 测试数据生成 ----------
def make_point(lat, lon, ts_offset_min=0, activity=None):
    """生成测试用轨迹点。"""
    base = datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
    ts = base + timedelta(minutes=ts_offset_min)
    return TrackPoint(
        latitude=lat, longitude=lon,
        timestamp=ts.isoformat(),
        source="test", activity=activity,
    )


def make_google_old_format(points_data):
    """生成旧格式 Google Location History JSON。"""
    locations = []
    for lat, lon, ts_ms in points_data:
        locations.append({
            "timestampMs": str(ts_ms),
            "latitudeE7": int(lat * 1e7),
            "longitudeE7": int(lon * 1e7),
            "accuracy": 10,
        })
    return {"locations": locations}


def make_gpx_content(points_data):
    """生成测试用 GPX 内容。"""
    pts = ""
    for lat, lon, time_str in points_data:
        pts += f'<trkpt lat="{lat}" lon="{lon}"><time>{time_str}</time></trkpt>\n'
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="test">
<trk><name>Test Track</name><trkseg>{pts}</trkseg></trk>
</gpx>"""


# ---------- Parser 测试 ----------
class TestParser:
    def test_track_point_creation(self):
        p = TrackPoint(latitude=31.23, longitude=121.47, timestamp="2024-01-01T00:00:00+00:00")
        assert p.latitude == 31.23
        assert p.longitude == 121.47
        assert p.source == "unknown"

    def test_parse_google_old_format(self):
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        data = make_google_old_format([
            (31.23, 121.47, base_ts),
            (31.24, 121.48, base_ts + 60000),
            (31.25, 121.49, base_ts + 120000),
        ])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fpath = f.name
        try:
            points = LocationParser.parse_file(fpath)
            assert len(points) == 3
            assert points[0].latitude == 31.23
            assert points[0].source == "google"
            assert points[0].accuracy == 10
        finally:
            os.unlink(fpath)

    def test_parse_gpx(self):
        data = make_gpx_content([
            (31.23, 121.47, "2024-01-01T10:00:00Z"),
            (31.24, 121.48, "2024-01-01T10:01:00Z"),
        ])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".gpx", delete=False) as f:
            f.write(data)
            fpath = f.name
        try:
            points = LocationParser.parse_file(fpath)
            assert len(points) == 2
            assert points[0].source == "gpx"
            assert abs(points[0].latitude - 31.23) < 0.001
        finally:
            os.unlink(fpath)

    def test_parse_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            LocationParser.parse_file("/nonexistent/file.json")

    def test_parse_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个GPX文件
            gpx_path = os.path.join(tmpdir, "track.gpx")
            with open(gpx_path, "w") as f:
                f.write(make_gpx_content([(31.23, 121.47, "2024-01-01T10:00:00Z")]))
            points = LocationParser.parse_directory(tmpdir)
            assert len(points) >= 1

    def test_skip_zero_coordinates(self):
        base_ts = int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
        data = make_google_old_format([
            (0, 0, base_ts),  # 应被跳过
            (31.23, 121.47, base_ts + 60000),
        ])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fpath = f.name
        try:
            points = LocationParser.parse_file(fpath)
            assert len(points) == 1
        finally:
            os.unlink(fpath)


# ---------- Analyzer 测试 ----------
class TestAnalyzer:
    def test_haversine(self):
        # 北京到上海约 1068 km
        dist = TrackAnalyzer.haversine_km(39.9042, 116.4074, 31.2304, 121.4737)
        assert 1000 < dist < 1150

    def test_empty_points(self):
        analyzer = TrackAnalyzer([])
        stats = analyzer.compute_statistics()
        assert stats["summary"]["total_points"] == 0
        assert analyzer.detect_stay_points() == []
        assert analyzer.segment_trips() == []

    def test_stay_point_detection(self):
        # 在同一位置停留30分钟
        points = [make_point(31.23, 121.47, i) for i in range(30)]
        analyzer = TrackAnalyzer(points)
        stays = analyzer.detect_stay_points(distance_threshold_m=200, duration_threshold_min=10)
        assert len(stays) >= 1
        assert stays[0].duration_minutes >= 20

    def test_no_stay_for_short_duration(self):
        # 只停留5分钟，不应被识别为停留点
        points = [make_point(31.23, 121.47, i) for i in range(5)]
        analyzer = TrackAnalyzer(points)
        stays = analyzer.detect_stay_points(duration_threshold_min=15)
        assert len(stays) == 0

    def test_trip_segmentation(self):
        # 两段行程，中间有大时间间隔
        points = []
        # 第一段：10个点，每分钟一个
        for i in range(10):
            points.append(make_point(31.23 + i * 0.001, 121.47, i))
        # 大间隔（3小时）
        for i in range(10):
            points.append(make_point(39.90 + i * 0.001, 116.40, 200 + i))
        analyzer = TrackAnalyzer(points)
        segments = analyzer.segment_trips(gap_threshold_min=120)
        assert len(segments) >= 2

    def test_statistics(self):
        points = [make_point(31.23 + i * 0.01, 121.47 + i * 0.01, i * 10) for i in range(20)]
        analyzer = TrackAnalyzer(points)
        stats = analyzer.compute_statistics()
        assert stats["summary"]["total_points"] == 20
        assert stats["summary"]["total_distance_km"] > 0
        assert stats["summary"]["active_days"] >= 1
        assert "daily" in stats
        assert "monthly" in stats

    def test_filter_by_year(self):
        points_2023 = [TrackPoint(31.23, 121.47, "2023-06-15T10:00:00+00:00", source="t")]
        points_2024 = [TrackPoint(31.23, 121.47, "2024-06-15T10:00:00+00:00", source="t")]
        analyzer = TrackAnalyzer(points_2023 + points_2024)
        filtered = analyzer.filter_by_year(2024)
        assert len(filtered.points) == 1

    def test_heatmap_data(self):
        points = [make_point(31.23, 121.47, i) for i in range(10)]
        analyzer = TrackAnalyzer(points)
        heat = analyzer.heatmap_data(grid_size=0.1)
        assert len(heat) >= 1
        assert "lat" in heat[0]
        assert "lng" in heat[0]
        assert "intensity" in heat[0]


# ---------- Exporter 测试 ----------
class TestExporter:
    def _make_exporter(self):
        points = [make_point(31.23 + i * 0.001, 121.47 + i * 0.001, i) for i in range(10)]
        return Exporter(points)

    def test_to_geojson(self):
        exporter = self._make_exporter()
        geojson = exporter.to_geojson()
        data = json.loads(geojson)
        assert data["type"] == "FeatureCollection"
        assert "features" in data
        # 至少有轨迹线
        assert any(f["geometry"]["type"] == "LineString" for f in data["features"])

    def test_to_csv(self):
        exporter = self._make_exporter()
        csv_content = exporter.to_csv()
        assert "timestamp" in csv_content
        assert "latitude" in csv_content
        lines = csv_content.strip().split("\n")
        assert len(lines) == 11  # header + 10 points

    def test_to_html(self):
        exporter = self._make_exporter()
        html = exporter.to_html(title="Test Report")
        assert "<!DOCTYPE html>" in html
        assert "Test Report" in html
        assert "leaflet" in html.lower()
        assert "TRACK_DATA" in html

    def test_save_files(self):
        exporter = self._make_exporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = os.path.join(tmpdir, "report.html")
            geojson_path = os.path.join(tmpdir, "track.geojson")
            csv_path = os.path.join(tmpdir, "track.csv")

            exporter.save_html(html_path)
            exporter.save_geojson(geojson_path)
            exporter.save_csv(csv_path)

            assert os.path.exists(html_path)
            assert os.path.exists(geojson_path)
            assert os.path.exists(csv_path)
            assert os.path.getsize(html_path) > 1000

    def test_empty_exporter(self):
        exporter = Exporter([])
        stats = exporter.analyzer.compute_statistics()
        assert stats["summary"]["total_points"] == 0
        # HTML 仍应可生成
        html = exporter.to_html()
        assert "<!DOCTYPE html>" in html


# ---------- 集成测试 ----------
class TestIntegration:
    def test_full_pipeline(self):
        """完整流程：解析 -> 分析 -> 导出。"""
        base_ts = int(datetime(2024, 6, 15, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)
        data = make_google_old_format([
            (31.23, 121.47, base_ts + i * 60000) for i in range(30)
        ] + [
            (39.90, 116.40, base_ts + 5000 * 60000 + i * 60000) for i in range(20)
        ])

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            fpath = f.name

        try:
            # 解析
            points = LocationParser.parse_file(fpath)
            assert len(points) == 50

            # 分析
            analyzer = TrackAnalyzer(points)
            stats = analyzer.compute_statistics()
            assert stats["summary"]["total_points"] == 50

            stays = analyzer.detect_stay_points()
            assert len(stays) >= 1

            # 导出
            exporter = Exporter(points, analyzer)
            html = exporter.to_html()
            assert len(html) > 1000

            geojson = exporter.to_geojson()
            assert json.loads(geojson)["type"] == "FeatureCollection"
        finally:
            os.unlink(fpath)
