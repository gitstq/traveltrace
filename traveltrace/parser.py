"""
数据解析模块 - 支持 Google Location History、GPX、照片EXIF 三种数据源
Data parser module - supports Google Location History, GPX tracks, and photo EXIF.
"""

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class TrackPoint:
    """单个轨迹点 / A single track point."""
    latitude: float
    longitude: float
    timestamp: str  # ISO 8601
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    velocity: Optional[float] = None
    heading: Optional[float] = None
    source: str = "unknown"  # google / gpx / exif
    activity: Optional[str] = None  # detected activity type

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @property
    def dt(self) -> datetime:
        return datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))


class LocationParser:
    """多源位置数据解析器 / Multi-source location data parser."""

    # ---------- 公共入口 ----------
    @staticmethod
    def parse_file(filepath: str) -> List[TrackPoint]:
        """自动识别文件类型并解析 / Auto-detect file type and parse."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        ext = path.suffix.lower()
        if ext == ".json":
            # 尝试 Google Location History 格式
            return LocationParser._parse_google_json(filepath)
        elif ext == ".gpx":
            return LocationParser._parse_gpx(filepath)
        elif ext in (".jpg", ".jpeg", ".png", ".heic"):
            return LocationParser._parse_exif(filepath)
        else:
            # 尝试按内容识别
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                head = f.read(200)
            if head.lstrip().startswith("<"):
                return LocationParser._parse_gpx(filepath)
            if head.lstrip().startswith("{"):
                return LocationParser._parse_google_json(filepath)
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def parse_directory(dirpath: str) -> List[TrackPoint]:
        """递归解析目录下所有支持的文件 / Recursively parse all supported files in a directory."""
        points: List[TrackPoint] = []
        supported = {".json", ".gpx", ".jpg", ".jpeg", ".png", ".heic"}
        for root, _, files in os.walk(dirpath):
            for fname in files:
                if Path(fname).suffix.lower() in supported:
                    fpath = os.path.join(root, fname)
                    try:
                        pts = LocationParser.parse_file(fpath)
                        points.extend(pts)
                    except Exception:
                        continue
        points.sort(key=lambda p: p.timestamp)
        return points

    # ---------- Google Location History ----------
    @staticmethod
    def _parse_google_json(filepath: str) -> List[TrackPoint]:
        """解析 Google Takeout 导出的 Location History JSON。
        支持两种格式：
        1. 旧格式: {"locations": [{timestampMs, latitudeE7, longitudeE7, ...}]}
        2. 新格式(Semantic): {"timelineObjects": [{activitySegment|placeVisit}]}
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        points: List[TrackPoint] = []

        # 旧格式
        if "locations" in data:
            for loc in data["locations"]:
                try:
                    ts_ms = int(loc.get("timestampMs", 0))
                    if ts_ms == 0:
                        ts_str = loc.get("timestamp", "")
                        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
                    lat = loc.get("latitudeE7", 0) / 1e7
                    lon = loc.get("longitudeE7", 0) / 1e7
                    if lat == 0 and lon == 0:
                        continue
                    point = TrackPoint(
                        latitude=lat,
                        longitude=lon,
                        timestamp=dt.isoformat(),
                        altitude=loc.get("altitude"),
                        accuracy=loc.get("accuracy"),
                        velocity=loc.get("velocity"),
                        heading=loc.get("heading"),
                        source="google",
                    )
                    points.append(point)
                except (ValueError, KeyError, TypeError):
                    continue

        # 新格式 Semantic Location History
        elif "timelineObjects" in data:
            for obj in data["timelineObjects"]:
                # activitySegment: 移动段
                if "activitySegment" in obj:
                    seg = obj["activitySegment"]
                    start_loc = seg.get("startLocation", {})
                    end_loc = seg.get("endLocation", {})
                    activity = seg.get("activityType", "").lower()
                    for loc_key, loc in [("start", start_loc), ("end", end_loc)]:
                        try:
                            lat = loc.get("latitudeE7", 0) / 1e7
                            lon = loc.get("longitudeE7", 0) / 1e7
                            if lat == 0 and lon == 0:
                                continue
                            ts = seg.get("duration", {}).get(
                                "startTimestamp" if loc_key == "start" else "endTimestamp", ""
                            )
                            points.append(TrackPoint(
                                latitude=lat, longitude=lon, timestamp=ts,
                                source="google", activity=activity,
                            ))
                        except (ValueError, KeyError, TypeError):
                            continue
                    # 路径中的经纬度点
                    waypoints = seg.get("waypointPath", {}).get("waypoints", [])
                    for wp in waypoints:
                        try:
                            lat = wp.get("latE7", 0) / 1e7
                            lon = wp.get("lngE7", 0) / 1e7
                            points.append(TrackPoint(
                                latitude=lat, longitude=lon,
                                timestamp=seg.get("duration", {}).get("startTimestamp", ""),
                                source="google", activity=activity,
                            ))
                        except (ValueError, KeyError, TypeError):
                            continue

                # placeVisit: 到访地点
                elif "placeVisit" in obj:
                    visit = obj["placeVisit"]
                    loc = visit.get("location", {})
                    try:
                        lat = loc.get("latitudeE7", 0) / 1e7
                        lon = loc.get("longitudeE7", 0) / 1e7
                        if lat == 0 and lon == 0:
                            continue
                        ts = visit.get("duration", {}).get("startTimestamp", "")
                        points.append(TrackPoint(
                            latitude=lat, longitude=lon, timestamp=ts,
                            source="google", activity="place_visit",
                        ))
                    except (ValueError, KeyError, TypeError):
                        continue

        points.sort(key=lambda p: p.timestamp)
        return points

    # ---------- GPX ----------
    @staticmethod
    def _parse_gpx(filepath: str) -> List[TrackPoint]:
        """解析 GPX 轨迹文件 / Parse GPX track file."""
        points: List[TrackPoint] = []
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            # 处理命名空间
            ns = ""
            if root.tag.startswith("{"):
                ns = root.tag.split("}")[0] + "}"

            for trk in root.iter(f"{ns}trk"):
                for trkseg in trk.iter(f"{ns}trkseg"):
                    for trkpt in trkseg.iter(f"{ns}trkpt"):
                        try:
                            lat = float(trkpt.get("lat", 0))
                            lon = float(trkpt.get("lon", 0))
                            if lat == 0 and lon == 0:
                                continue
                            ele_elem = trkpt.find(f"{ns}ele")
                            time_elem = trkpt.find(f"{ns}time")
                            altitude = float(ele_elem.text) if ele_elem is not None and ele_elem.text else None
                            timestamp = time_elem.text if time_elem is not None and time_elem.text else ""
                            if not timestamp:
                                timestamp = datetime.now(timezone.utc).isoformat()
                            points.append(TrackPoint(
                                latitude=lat, longitude=lon,
                                timestamp=timestamp, altitude=altitude,
                                source="gpx",
                            ))
                        except (ValueError, TypeError):
                            continue

            # 也处理 waypoints
            for wpt in root.iter(f"{ns}wpt"):
                try:
                    lat = float(wpt.get("lat", 0))
                    lon = float(wpt.get("lon", 0))
                    if lat == 0 and lon == 0:
                        continue
                    time_elem = wpt.find(f"{ns}time")
                    timestamp = time_elem.text if time_elem is not None and time_elem.text else datetime.now(timezone.utc).isoformat()
                    points.append(TrackPoint(
                        latitude=lat, longitude=lon, timestamp=timestamp, source="gpx",
                    ))
                except (ValueError, TypeError):
                    continue
        except ET.ParseError:
            pass

        points.sort(key=lambda p: p.timestamp)
        return points

    # ---------- EXIF ----------
    @staticmethod
    def _parse_exif(filepath: str) -> List[TrackPoint]:
        """从照片 EXIF 中提取 GPS 坐标 / Extract GPS coordinates from photo EXIF.
        仅使用标准库，不依赖 pillow。如果无法解析则返回空列表。
        """
        points: List[TrackPoint] = []
        try:
            gps, dt_str = LocationParser._extract_exif_gps(filepath)
            if gps:
                lat, lon = gps
                timestamp = dt_str or datetime.now(timezone.utc).isoformat()
                points.append(TrackPoint(
                    latitude=lat, longitude=lon, timestamp=timestamp, source="exif",
                ))
        except Exception:
            pass
        return points

    @staticmethod
    def _extract_exif_gps(filepath: str) -> Tuple[Optional[Tuple[float, float]], Optional[str]]:
        """极简 EXIF GPS 提取（仅处理 JPEG）。
        Returns ( (lat, lon) or None, datetime_string or None )
        """
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            # 检查 JPEG SOI
            if data[:2] != b"\xff\xd8":
                return None, None

            # 查找 APP1 (EXIF) 标记
            idx = 2
            while idx < len(data) - 4:
                if data[idx] != 0xFF:
                    idx += 1
                    continue
                marker = data[idx + 1]
                if marker == 0xE1:  # APP1
                    length = int.from_bytes(data[idx + 2:idx + 4], "big")
                    app1_data = data[idx + 4:idx + 2 + length]
                    if app1_data[:4] == b"Exif":
                        return LocationParser._parse_exif_ifd(app1_data[6:])
                    idx += 2 + length
                elif marker in (0xD9, 0xDA):  # EOI / SOS
                    break
                else:
                    length = int.from_bytes(data[idx + 2:idx + 4], "big") if idx + 4 < len(data) else 0
                    idx += 2 + length if length > 0 else 2
        except Exception:
            pass
        return None, None

    @staticmethod
    def _parse_exif_ifd(tiff_data: bytes) -> Tuple[Optional[Tuple[float, float]], Optional[str]]:
        """解析 TIFF IFD 结构提取 GPS 和时间。极简实现。"""
        try:
            byte_order = tiff_data[:2]
            if byte_order == b"II":
                endian = "<"
            elif byte_order == b"MM":
                endian = ">"
            else:
                return None, None

            ifd0_offset = int.from_bytes(tiff_data[4:8], endian)
            gps_info = None
            dt_str = None

            def read_ifd(offset):
                nonlocal gps_info, dt_str
                if offset + 2 > len(tiff_data):
                    return 0
                num_entries = int.from_bytes(tiff_data[offset:offset + 2], endian)
                next_ifd = 0
                for i in range(num_entries):
                    entry_off = offset + 2 + i * 12
                    if entry_off + 12 > len(tiff_data):
                        break
                    tag = int.from_bytes(tiff_data[entry_off:entry_off + 2], endian)
                    type_ = int.from_bytes(tiff_data[entry_off + 2:entry_off + 4], endian)
                    count = int.from_bytes(tiff_data[entry_off + 4:entry_off + 8], endian)
                    value_offset = tiff_data[entry_off + 8:entry_off + 12]

                    if tag == 0x8825:  # GPS IFD pointer
                        gps_ifd_off = int.from_bytes(value_offset, endian)
                        gps_info = LocationParser._parse_gps_ifd(tiff_data, gps_ifd_off, endian)
                    elif tag == 0x0132:  # DateTime
                        if type_ == 2:  # ASCII
                            val_off = int.from_bytes(value_offset, endian)
                            raw = tiff_data[val_off:val_off + count].decode("ascii", errors="ignore").strip("\x00 ")
                            try:
                                dt = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
                                dt_str = dt.isoformat()
                            except ValueError:
                                pass

                next_ifd_off = offset + 2 + num_entries * 12
                if next_ifd_off + 4 <= len(tiff_data):
                    next_ifd = int.from_bytes(tiff_data[next_ifd_off:next_ifd_off + 4], endian)
                return next_ifd

            next_off = read_ifd(ifd0_offset)
            # 不递归子IFD，GPS已通过指针获取
            return gps_info, dt_str
        except Exception:
            return None, None

    @staticmethod
    def _parse_gps_ifd(tiff_data: bytes, offset: int, endian: str) -> Optional[Tuple[float, float]]:
        """解析 GPS IFD。"""
        try:
            if offset + 2 > len(tiff_data):
                return None
            num_entries = int.from_bytes(tiff_data[offset:offset + 2], endian)
            lat_ref = "N"
            lon_ref = "E"
            lat_dms = None
            lon_dms = None

            for i in range(num_entries):
                entry_off = offset + 2 + i * 12
                if entry_off + 12 > len(tiff_data):
                    break
                tag = int.from_bytes(tiff_data[entry_off:entry_off + 2], endian)
                type_ = int.from_bytes(tiff_data[entry_off + 2:entry_off + 4], endian)
                count = int.from_bytes(tiff_data[entry_off + 4:entry_off + 8], endian)
                value_offset = tiff_data[entry_off + 8:entry_off + 12]

                if tag == 0x0001:  # GPSLatitudeRef
                    lat_ref = value_offset[:1].decode("ascii", errors="ignore").upper() or "N"
                elif tag == 0x0003:  # GPSLongitudeRef
                    lon_ref = value_offset[:1].decode("ascii", errors="ignore").upper() or "E"
                elif tag == 0x0002:  # GPSLatitude (3 RATIONALS)
                    val_off = int.from_bytes(value_offset, endian)
                    lat_dms = LocationParser._read_rationals(tiff_data, val_off, 3, endian)
                elif tag == 0x0004:  # GPSLongitude
                    val_off = int.from_bytes(value_offset, endian)
                    lon_dms = LocationParser._read_rationals(tiff_data, val_off, 3, endian)

            if lat_dms and lon_dms:
                lat = lat_dms[0] + lat_dms[1] / 60 + lat_dms[2] / 3600
                lon = lon_dms[0] + lon_dms[1] / 60 + lon_dms[2] / 3600
                if lat_ref == "S":
                    lat = -lat
                if lon_ref == "W":
                    lon = -lon
                return (lat, lon)
        except Exception:
            pass
        return None

    @staticmethod
    def _read_rationals(data: bytes, offset: int, count: int, endian: str) -> Optional[List[float]]:
        """读取 count 个 RATIONAL 值。"""
        try:
            result = []
            for i in range(count):
                off = offset + i * 8
                numerator = int.from_bytes(data[off:off + 4], endian)
                denominator = int.from_bytes(data[off + 4:off + 8], endian)
                result.append(numerator / denominator if denominator != 0 else 0.0)
            return result
        except Exception:
            return None
