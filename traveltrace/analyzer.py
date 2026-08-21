"""
数据分析模块 - 停留点识别、行程分段、统计聚合
Data analysis module - stay point detection, trip segmentation, statistics.
"""

import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional

from .parser import TrackPoint


@dataclass
class StayPoint:
    """停留点 / A location where the user stayed for a significant duration."""
    latitude: float
    longitude: float
    arrival_time: str
    departure_time: str
    duration_minutes: float
    point_count: int
    name: Optional[str] = None  # 可选地名（需反向地理编码，本工具不调用外部API）

    def to_dict(self) -> dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "arrival_time": self.arrival_time,
            "departure_time": self.departure_time,
            "duration_minutes": round(self.duration_minutes, 1),
            "point_count": self.point_count,
        }


@dataclass
class TripSegment:
    """一段行程 / A trip segment between two stay points."""
    start_time: str
    end_time: str
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    distance_km: float
    duration_minutes: float
    activity: Optional[str] = None
    point_count: int = 0

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start": [self.start_lat, self.start_lon],
            "end": [self.end_lat, self.end_lon],
            "distance_km": round(self.distance_km, 2),
            "duration_minutes": round(self.duration_minutes, 1),
            "activity": self.activity,
            "point_count": self.point_count,
        }


class TrackAnalyzer:
    """轨迹分析器 / Track analyzer."""

    def __init__(self, points: List[TrackPoint]):
        self.points = sorted(points, key=lambda p: p.timestamp)

    # ---------- 核心工具 ----------
    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine 公式计算两点间距离（公里）。"""
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # ---------- 停留点识别 ----------
    def detect_stay_points(
        self,
        distance_threshold_m: float = 100.0,
        duration_threshold_min: float = 15.0,
    ) -> List[StayPoint]:
        """
        识别停留点：在一定距离范围内停留超过阈值时间。
        算法：经典时间-空间聚类（Li et al.）
        """
        if not self.points:
            return []

        stay_points: List[StayPoint] = []
        i = 0
        n = len(self.points)

        while i < n:
            j = i + 1
            while j < n:
                dist = self.haversine_km(
                    self.points[i].latitude, self.points[i].longitude,
                    self.points[j].latitude, self.points[j].longitude,
                ) * 1000  # to meters
                if dist > distance_threshold_m:
                    break
                j += 1

            if j > i + 1:
                try:
                    t1 = self.points[i].dt
                    t2 = self.points[j - 1].dt
                    duration = (t2 - t1).total_seconds() / 60.0
                    if duration >= duration_threshold_min:
                        # 计算质心
                        cluster = self.points[i:j]
                        avg_lat = sum(p.latitude for p in cluster) / len(cluster)
                        avg_lon = sum(p.longitude for p in cluster) / len(cluster)
                        stay_points.append(StayPoint(
                            latitude=round(avg_lat, 6),
                            longitude=round(avg_lon, 6),
                            arrival_time=self.points[i].timestamp,
                            departure_time=self.points[j - 1].timestamp,
                            duration_minutes=duration,
                            point_count=len(cluster),
                        ))
                except (ValueError, TypeError):
                    pass
                i = j
            else:
                i += 1

        return stay_points

    # ---------- 行程分段 ----------
    def segment_trips(
        self,
        gap_threshold_min: float = 120.0,
        distance_threshold_km: float = 0.5,
    ) -> List[TripSegment]:
        """
        将轨迹切分为多段行程。
        依据：时间间隔超过阈值 或 距离跳跃超过阈值。
        """
        if len(self.points) < 2:
            return []

        segments: List[TripSegment] = []
        seg_start = 0

        for i in range(1, len(self.points)):
            try:
                t_prev = self.points[i - 1].dt
                t_curr = self.points[i].dt
                time_gap = (t_curr - t_prev).total_seconds() / 60.0
                dist = self.haversine_km(
                    self.points[i - 1].latitude, self.points[i - 1].longitude,
                    self.points[i].latitude, self.points[i].longitude,
                )
            except (ValueError, TypeError):
                time_gap = 0
                dist = 0

            if time_gap > gap_threshold_min or dist > distance_threshold_km * 10:
                # 结束当前段
                if i - 1 > seg_start:
                    seg = self._build_segment(seg_start, i - 1)
                    if seg:
                        segments.append(seg)
                seg_start = i

        # 最后一段
        if len(self.points) - 1 > seg_start:
            seg = self._build_segment(seg_start, len(self.points) - 1)
            if seg:
                segments.append(seg)

        return segments

    def _build_segment(self, start_idx: int, end_idx: int) -> Optional[TripSegment]:
        if start_idx >= end_idx:
            return None
        cluster = self.points[start_idx:end_idx + 1]
        total_dist = 0.0
        for k in range(1, len(cluster)):
            total_dist += self.haversine_km(
                cluster[k - 1].latitude, cluster[k - 1].longitude,
                cluster[k].latitude, cluster[k].longitude,
            )
        try:
            duration = (cluster[-1].dt - cluster[0].dt).total_seconds() / 60.0
        except (ValueError, TypeError):
            duration = 0
        activity = cluster[0].activity
        return TripSegment(
            start_time=cluster[0].timestamp,
            end_time=cluster[-1].timestamp,
            start_lat=cluster[0].latitude,
            start_lon=cluster[0].longitude,
            end_lat=cluster[-1].latitude,
            end_lon=cluster[-1].longitude,
            distance_km=total_dist,
            duration_minutes=duration,
            activity=activity,
            point_count=len(cluster),
        )

    # ---------- 统计聚合 ----------
    def compute_statistics(self) -> Dict:
        """计算全面的旅行统计 / Compute comprehensive travel statistics."""
        if not self.points:
            return self._empty_stats()

        total_distance = 0.0
        for i in range(1, len(self.points)):
            total_distance += self.haversine_km(
                self.points[i - 1].latitude, self.points[i - 1].longitude,
                self.points[i].latitude, self.points[i].longitude,
            )

        # 时间范围
        times = []
        for p in self.points:
            try:
                times.append(p.dt)
            except (ValueError, TypeError):
                pass

        if not times:
            return self._empty_stats()

        min_time = min(times)
        max_time = max(times)
        total_days = (max_time - min_time).days + 1

        # 按天统计
        daily_stats = defaultdict(lambda: {"distance": 0.0, "points": 0})
        for i in range(1, len(self.points)):
            try:
                day = self.points[i].dt.strftime("%Y-%m-%d")
                dist = self.haversine_km(
                    self.points[i - 1].latitude, self.points[i - 1].longitude,
                    self.points[i].latitude, self.points[i].longitude,
                )
                daily_stats[day]["distance"] += dist
                daily_stats[day]["points"] += 1
            except (ValueError, TypeError):
                continue

        # 按月份统计
        monthly_stats = defaultdict(lambda: {"distance": 0.0, "points": 0, "days": set()})
        for day, info in daily_stats.items():
            month = day[:7]
            monthly_stats[month]["distance"] += info["distance"]
            monthly_stats[month]["points"] += info["points"]
            monthly_stats[month]["days"].add(day)

        # 活动类型统计
        activity_stats = defaultdict(int)
        for p in self.points:
            if p.activity:
                activity_stats[p.activity] += 1

        # 经纬度范围（bounding box）
        lats = [p.latitude for p in self.points]
        lons = [p.longitude for p in self.points]

        # 活跃天数（有数据的天数）
        active_days = len(daily_stats)

        # 停留点
        stay_points = self.detect_stay_points()
        unique_stay_locations = len(set(
            (round(sp.latitude, 2), round(sp.longitude, 2)) for sp in stay_points
        ))

        return {
            "summary": {
                "total_points": len(self.points),
                "total_distance_km": round(total_distance, 2),
                "date_range_start": min_time.isoformat(),
                "date_range_end": max_time.isoformat(),
                "total_days": total_days,
                "active_days": active_days,
                "stay_points_count": len(stay_points),
                "unique_stay_locations": unique_stay_locations,
                "bounding_box": {
                    "min_lat": min(lats),
                    "max_lat": max(lats),
                    "min_lon": min(lons),
                    "max_lon": max(lons),
                },
            },
            "daily": {
                day: {"distance_km": round(v["distance"], 2), "points": v["points"]}
                for day, v in sorted(daily_stats.items())
            },
            "monthly": {
                month: {
                    "distance_km": round(v["distance"], 2),
                    "points": v["points"],
                    "active_days": len(v["days"]),
                }
                for month, v in sorted(monthly_stats.items())
            },
            "activities": dict(activity_stats),
            "sources": self._source_stats(),
        }

    def _source_stats(self) -> Dict[str, int]:
        stats = defaultdict(int)
        for p in self.points:
            stats[p.source] += 1
        return dict(stats)

    @staticmethod
    def _empty_stats() -> Dict:
        return {
            "summary": {
                "total_points": 0, "total_distance_km": 0,
                "date_range_start": "", "date_range_end": "",
                "total_days": 0, "active_days": 0,
                "stay_points_count": 0, "unique_stay_locations": 0,
                "bounding_box": {},
            },
            "daily": {}, "monthly": {}, "activities": {}, "sources": {},
        }

    # ---------- 热力图数据 ----------
    def heatmap_data(self, grid_size: float = 0.01) -> List[Dict]:
        """生成热力图数据（网格化聚合）。
        grid_size: 网格大小（度），0.01 ≈ 1.1km
        """
        grids = defaultdict(int)
        for p in self.points:
            grid_lat = round(p.latitude / grid_size) * grid_size
            grid_lon = round(p.longitude / grid_size) * grid_size
            grids[(grid_lat, grid_lon)] += 1

        max_count = max(grids.values()) if grids else 1
        return [
            {"lat": lat, "lng": lon, "count": count, "intensity": round(count / max_count, 3)}
            for (lat, lon), count in grids.items()
        ]

    # ---------- 按年份筛选 ----------
    def filter_by_year(self, year: int) -> "TrackAnalyzer":
        """筛选指定年份的数据。"""
        filtered = []
        for p in self.points:
            try:
                if p.dt.year == year:
                    filtered.append(p)
            except (ValueError, TypeError):
                continue
        return TrackAnalyzer(filtered)

    def filter_by_date_range(self, start: str, end: str) -> "TrackAnalyzer":
        """按日期范围筛选（YYYY-MM-DD）。"""
        try:
            start_dt = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
            end_dt = datetime.fromisoformat(end).replace(tzinfo=timezone.utc) + timedelta(days=1)
        except ValueError:
            return self
        filtered = []
        for p in self.points:
            try:
                if start_dt <= p.dt < end_dt:
                    filtered.append(p)
            except (ValueError, TypeError):
                continue
        return TrackAnalyzer(filtered)
