"""canvas_layout.yaml 배치표로 건물 배경 + 자산 값 박스를 가진 Grafana 대시보드 JSON을 만든다."""
import json
from pathlib import Path

import yaml

LAYOUT = Path("canvas_layout.yaml")
OUT = Path("epms-canvas-building.json")
DATASOURCE_UID = "eg18i4yqw51q8a"

cfg = yaml.safe_load(LAYOUT.read_text(encoding="utf-8"))
bg = cfg["background"]
vb = cfg["value_box"]


def element_pair(item: dict) -> list[dict]:
    name = item["point"].replace("PT_", "")
    x, y = item["x"], item["y"]
    w = item.get("width", vb["width"])
    h = vb["height"]

    label = {
        "type": "rectangle",
        "name": f"{name}_BOX",
        "config": {
            "text": {"fixed": item["label"], "mode": "fixed"},
            "color": {"fixed": "#E5E7EB"},
            "align": "center", "valign": "top", "size": 12,
        },
        "background": {"color": {"fixed": "#111827"}},
        "border": {"color": {"fixed": "#4B5563"}},
        "constraint": {"horizontal": "left", "vertical": "top"},
        "placement": {"left": x, "top": y, "width": w, "height": h, "rotation": 0},
    }
    value = {
        "type": "metric-value",
        "name": f"{name}_VAL",
        "config": {
            "text": {"field": item["point"], "mode": "field", "fixed": ""},
            "color": {"fixed": "#34D399"},
            "align": "center", "valign": "middle", "size": 18,
        },
        "background": {"color": {"fixed": "transparent"}},
        "constraint": {"horizontal": "left", "vertical": "top"},
        "placement": {"left": x, "top": y + 18, "width": w, "height": h - 18, "rotation": 0},
    }
    return [label, value]


elements = [e for item in cfg["items"] for e in element_pair(item)]

root = {
    "type": "frame",
    "name": "Element root",
    "background": {
        "color": {"fixed": bg["color"]},
        "image": {"fixed": bg["url"], "mode": "fixed"},
    },
    "elements": elements,
}

pivot_query = (
    'from(bucket: "node_red_bucket") |> range(start: -1m) '
    '|> filter(fn: (r) => r._measurement == "epms" and r._field == "value") '
    '|> last() '
    '|> pivot(rowKey: ["_time"], columnKey: ["point_id"], valueColumn: "_value")'
)

dashboard = {
    "uid": "epms-canvas-building",
    "title": "EPMS 건물 단선도 (배경 이미지)",
    "tags": ["EPMS", "demo"],
    "timezone": "Asia/Seoul",
    "schemaVersion": 40,
    "version": 1,
    "refresh": "5s",
    "time": {"from": "now-1h", "to": "now"},
    "panels": [
        {
            "id": 1,
            "type": "canvas",
            "title": "EPMS 건물 단선도",
            "gridPos": {"h": 25, "w": 24, "x": 0, "y": 0},
            "datasource": {"type": "influxdb", "uid": DATASOURCE_UID},
            "targets": [{"refId": "A", "query": pivot_query}],
            "fieldConfig": {
                "defaults": {
                    "decimals": 1,
                    "mappings": [],
                    "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                },
                "overrides": [],
            },
            "options": {
                "inlineEditing": True,
                "showAdvancedTypes": True,
                "panZoom": False,
                "root": root,
            },
        }
    ],
}

OUT.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"generated: {OUT} ({len(cfg['items'])} items)")
