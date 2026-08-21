"""
命令行接口 / Command-line interface.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List

from .parser import LocationParser, TrackPoint
from .analyzer import TrackAnalyzer
from .exporter import Exporter
from . import __version__


def cmd_parse(args):
    """解析数据并输出统计 / Parse data and print statistics."""
    points = _load_points(args.input)
    if not points:
        print("⚠️  未找到有效的轨迹点数据", file=sys.stderr)
        sys.exit(1)

    analyzer = TrackAnalyzer(points)
    stats = analyzer.compute_statistics()
    summary = stats["summary"]

    print(f"\n{'='*50}")
    print(f"  📍 TravelTrace 旅行足迹分析报告")
    print(f"{'='*50}")
    print(f"  数据源:        {args.input}")
    print(f"  轨迹点总数:    {summary['total_points']:,}")
    print(f"  总行程距离:    {summary['total_distance_km']:,} km")
    print(f"  时间范围:      {summary['date_range_start'][:10]} ~ {summary['date_range_end'][:10]}")
    print(f"  总天数:        {summary['total_days']} 天")
    print(f"  活跃天数:      {summary['active_days']} 天")
    print(f"  停留点数量:    {summary['stay_points_count']}")
    print(f"  独立停留位置:  {summary['unique_stay_locations']}")
    print(f"  数据来源:      {', '.join(f'{k}({v})' for k,v in stats['sources'].items())}")
    print(f"{'='*50}\n")

    if args.verbose:
        print("📅 月度统计:")
        for month, info in stats.get("monthly", {}).items():
            print(f"  {month}: {info['distance_km']:>8.1f} km | {info['active_days']} 天活跃 | {info['points']} 点")
        print()

    if args.output:
        if args.output.endswith(".json"):
            Path(args.output).write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        elif args.output.endswith(".csv"):
            Exporter(points, analyzer).save_csv(args.output)
        print(f"✅ 统计已保存到: {args.output}")


def cmd_visualize(args):
    """生成交互式 HTML 可视化报告 / Generate interactive HTML visualization."""
    points = _load_points(args.input)
    if not points:
        print("⚠️  未找到有效的轨迹点数据", file=sys.stderr)
        sys.exit(1)

    analyzer = TrackAnalyzer(points)
    if args.year:
        analyzer = analyzer.filter_by_year(args.year)
        points = analyzer.points

    exporter = Exporter(points, analyzer)
    title = args.title or f"My Travel Trace {args.year or ''}"
    output = args.output or "travel_trace_report.html"
    exporter.save_html(output, title)
    print(f"✅ 可视化报告已生成: {output}")
    print(f"   用浏览器打开即可查看交互式地图")

    if args.serve:
        _start_server(output, args.port)


def cmd_export(args):
    """导出为 GeoJSON / CSV / HTML / Export to GeoJSON/CSV/HTML."""
    points = _load_points(args.input)
    if not points:
        print("⚠️  未找到有效的轨迹点数据", file=sys.stderr)
        sys.exit(1)

    analyzer = TrackAnalyzer(points)
    exporter = Exporter(points, analyzer)

    fmt = args.format.lower()
    output = args.output or f"travel_trace.{fmt}"

    if fmt == "geojson":
        exporter.save_geojson(output)
    elif fmt == "csv":
        if args.stats:
            Path(output).write_text(exporter.stats_to_csv(), encoding="utf-8")
        else:
            exporter.save_csv(output)
    elif fmt == "html":
        exporter.save_html(output, args.title or "My Travel Trace")
    else:
        print(f"❌ 不支持的格式: {fmt}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ 已导出为 {fmt.upper()}: {output}")


def cmd_stays(args):
    """识别并输出停留点 / Detect and output stay points."""
    points = _load_points(args.input)
    if not points:
        print("⚠️  未找到有效的轨迹点数据", file=sys.stderr)
        sys.exit(1)

    analyzer = TrackAnalyzer(points)
    stays = analyzer.detect_stay_points(
        distance_threshold_m=args.distance,
        duration_threshold_min=args.duration,
    )

    print(f"\n📍 识别到 {len(stays)} 个停留点 (距离阈值={args.distance}m, 时长阈值={args.duration}min)\n")
    for i, sp in enumerate(stays, 1):
        print(f"  {i:3d}. ({sp.latitude:.5f}, {sp.longitude:.5f})")
        print(f"       到达: {sp.arrival_time[:19]} | 离开: {sp.departure_time[:19]}")
        print(f"       停留: {sp.duration_minutes:.1f} 分钟 | 数据点: {sp.point_count}")

    if args.output:
        data = [sp.to_dict() for sp in stays]
        Path(args.output).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ 停留点已保存到: {args.output}")


def cmd_serve(args):
    """启动 Web 可视化服务器 / Start web visualization server."""
    from .web.server import start_server
    points = _load_points(args.input) if args.input else []
    start_server(points, host=args.host, port=args.port)


def _load_points(input_path: str) -> List[TrackPoint]:
    """加载数据（文件或目录）。"""
    if not input_path:
        print("❌ 请指定输入文件或目录 (-i/--input)", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)

    if os.path.isdir(input_path):
        print(f"📂 扫描目录: {input_path}")
        return LocationParser.parse_directory(input_path)
    else:
        return LocationParser.parse_file(input_path)


def _start_server(html_file: str, port: int):
    """启动简易 HTTP 服务器预览 HTML。"""
    import http.server
    import socketserver
    import webbrowser

    handler = http.server.SimpleHTTPRequestHandler
    os.chdir(os.path.dirname(os.path.abspath(html_file)) or ".")
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}/{os.path.basename(html_file)}"
        print(f"🌐 预览服务器已启动: {url}")
        print(f"   按 Ctrl+C 停止")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        httpd.serve_forever()


def main():
    parser = argparse.ArgumentParser(
        prog="traveltrace",
        description="📍 TravelTrace - 旅行足迹智能可视化引擎 | Intelligent Travel Footprint Visualization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例 / Examples:
  traveltrace parse -i location_history.json -v
  traveltrace visualize -i location_history.json -o report.html
  traveltrace visualize -i ./takeout/ --year 2024 --serve
  traveltrace export -i track.gpx -f geojson -o track.geojson
  traveltrace stays -i location_history.json --distance 150 --duration 20
  traveltrace serve -i location_history.json --port 8080
        """,
    )
    parser.add_argument("--version", action="version", version=f"TravelTrace v{__version__}")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # parse
    p_parse = subparsers.add_parser("parse", help="解析数据并输出统计")
    p_parse.add_argument("-i", "--input", required=True, help="输入文件或目录")
    p_parse.add_argument("-o", "--output", help="输出统计文件 (JSON/CSV)")
    p_parse.add_argument("-v", "--verbose", action="store_true", help="显示详细月度统计")
    p_parse.set_defaults(func=cmd_parse)

    # visualize
    p_viz = subparsers.add_parser("visualize", help="生成交互式HTML可视化报告")
    p_viz.add_argument("-i", "--input", required=True, help="输入文件或目录")
    p_viz.add_argument("-o", "--output", help="输出HTML文件路径")
    p_viz.add_argument("-t", "--title", help="报告标题")
    p_viz.add_argument("--year", type=int, help="仅筛选指定年份")
    p_viz.add_argument("--serve", action="store_true", help="生成后启动预览服务器")
    p_viz.add_argument("--port", type=int, default=8000, help="预览服务器端口 (默认8000)")
    p_viz.set_defaults(func=cmd_visualize)

    # export
    p_exp = subparsers.add_parser("export", help="导出为 GeoJSON/CSV/HTML")
    p_exp.add_argument("-i", "--input", required=True, help="输入文件或目录")
    p_exp.add_argument("-f", "--format", required=True, choices=["geojson", "csv", "html"], help="导出格式")
    p_exp.add_argument("-o", "--output", help="输出文件路径")
    p_exp.add_argument("-t", "--title", help="HTML报告标题")
    p_exp.add_argument("--stats", action="store_true", help="CSV格式时导出统计而非原始点")
    p_exp.set_defaults(func=cmd_export)

    # stays
    p_stays = subparsers.add_parser("stays", help="识别停留点")
    p_stays.add_argument("-i", "--input", required=True, help="输入文件或目录")
    p_stays.add_argument("-d", "--distance", type=float, default=100.0, help="距离阈值(米), 默认100")
    p_stays.add_argument("--duration", type=float, default=15.0, help="时长阈值(分钟), 默认15")
    p_stays.add_argument("-o", "--output", help="输出停留点JSON")
    p_stays.set_defaults(func=cmd_stays)

    # serve
    p_serve = subparsers.add_parser("serve", help="启动Web可视化服务器")
    p_serve.add_argument("-i", "--input", help="预加载数据文件")
    p_serve.add_argument("--host", default="0.0.0.0", help="监听地址 (默认0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="监听端口 (默认8000)")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
