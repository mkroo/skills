#!/usr/bin/env python3
"""Check OG image dimensions, file size, and format.

Usage:
    python3 check_image.py <image_url_or_path>

Downloads the image (if URL) and validates:
- Dimensions (width x height)
- Aspect ratio
- File size
- Format (JPEG, PNG, etc.)
- Platform compatibility

Output: JSON with image metadata and validation results.

Dependencies: stdlib only (no pip install needed).
Uses struct-based header parsing for PNG/JPEG/GIF/WebP dimensions.
"""

import json
import os
import struct
import sys
import tempfile
import urllib.request
import urllib.error


def get_png_dimensions(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if len(data) < 24:
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def get_jpeg_dimensions(data):
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            if i + 9 < len(data):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return w, h
        if marker == 0xD9 or marker == 0xDA:
            break
        if i + 3 < len(data):
            length = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + length
        else:
            break
    return None


def get_gif_dimensions(data):
    if data[:4] not in (b"GIF8",):
        return None
    if len(data) < 10:
        return None
    w, h = struct.unpack("<HH", data[6:10])
    return w, h


def get_webp_dimensions(data):
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    if data[12:16] == b"VP8 " and len(data) >= 30:
        w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return w, h
    if data[12:16] == b"VP8L" and len(data) >= 25:
        bits = struct.unpack("<I", data[21:25])[0]
        w = (bits & 0x3FFF) + 1
        h = ((bits >> 14) & 0x3FFF) + 1
        return w, h
    if data[12:16] == b"VP8X" and len(data) >= 30:
        w = (struct.unpack("<I", data[24:27] + b"\x00")[0] & 0xFFFFFF) + 1
        h = (struct.unpack("<I", data[27:30] + b"\x00")[0] & 0xFFFFFF) + 1
        return w, h
    return None


def get_image_format(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if data[:2] == b"\xff\xd8":
        return "JPEG"
    if data[:4] == b"GIF8":
        return "GIF"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "WebP"
    if data[:4] == b"<svg" or b"<svg" in data[:256]:
        return "SVG"
    return "UNKNOWN"


def get_dimensions(data):
    fmt = get_image_format(data)
    if fmt == "PNG":
        return get_png_dimensions(data)
    elif fmt == "JPEG":
        return get_jpeg_dimensions(data)
    elif fmt == "GIF":
        return get_gif_dimensions(data)
    elif fmt == "WebP":
        return get_webp_dimensions(data)
    return None


PLATFORM_SPECS = {
    "kakaotalk": {"min_w": 80, "min_h": 80, "rec_w": 800, "rec_h": 400, "max_kb": 500, "ratio": 2.0},
    "facebook": {"min_w": 600, "min_h": 315, "rec_w": 1200, "rec_h": 630, "max_kb": 8192, "ratio": 1.91},
    "twitter": {"min_w": 400, "min_h": 400, "rec_w": 1200, "rec_h": 628, "max_kb": 5120, "ratio": 2.0},
    "discord": {"min_w": 400, "min_h": 300, "rec_w": 1200, "rec_h": 630, "max_kb": 8192, "ratio": 1.91},
    "slack": {"min_w": 400, "min_h": 400, "rec_w": 1200, "rec_h": 630, "max_kb": 5120, "ratio": 1.91},
    "linkedin": {"min_w": 200, "min_h": 200, "rec_w": 1200, "rec_h": 627, "max_kb": 5120, "ratio": 1.91},
    "whatsapp": {"min_w": 300, "min_h": 200, "rec_w": 1200, "rec_h": 630, "max_kb": 200, "ratio": 1.91},
}


def validate_image(width, height, file_size_bytes, fmt):
    issues = []
    file_size_kb = file_size_bytes / 1024
    ratio = width / height if height > 0 else 0

    # Universal checks
    if width < 1200 or height < 630:
        issues.append({
            "severity": "WARN",
            "rule": "W1",
            "message": f"Image {width}x{height} is below recommended 1200x630",
        })

    if file_size_kb > 500:
        issues.append({
            "severity": "WARN",
            "rule": "W2",
            "message": f"Image {file_size_kb:.0f}KB exceeds 500KB (KakaoTalk limit)",
        })

    if abs(ratio - 1.91) > 0.15 and abs(ratio - 2.0) > 0.15:
        issues.append({
            "severity": "WARN",
            "rule": "W3",
            "message": f"Aspect ratio {ratio:.2f}:1 deviates from recommended 1.91:1 ~ 2:1",
        })

    if fmt == "SVG":
        issues.append({
            "severity": "WARN",
            "rule": "W1",
            "message": "SVG format may not be supported by all platforms; prefer JPG or PNG",
        })

    # Per-platform checks
    platform_results = {}
    for name, spec in PLATFORM_SPECS.items():
        platform_issues = []
        if width < spec["min_w"] or height < spec["min_h"]:
            platform_issues.append(f"Below minimum {spec['min_w']}x{spec['min_h']}")
        if file_size_kb > spec["max_kb"]:
            platform_issues.append(f"Exceeds {spec['max_kb']}KB limit")
        platform_results[name] = {
            "compatible": len(platform_issues) == 0,
            "issues": platform_issues,
        }

    return issues, platform_results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: check_image.py <image_url_or_path>"}, ensure_ascii=False))
        sys.exit(1)

    target = sys.argv[1]
    data = None
    file_size = 0

    try:
        if target.startswith("http://") or target.startswith("https://"):
            req = urllib.request.Request(target, headers={"User-Agent": "OGValidatorBot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
                file_size = len(data)
        else:
            with open(target, "rb") as f:
                data = f.read()
                file_size = len(data)
    except urllib.error.HTTPError as e:
        print(json.dumps({"error": f"HTTP error fetching image: {e.code} {e.reason}", "accessible": False}, ensure_ascii=False))
        sys.exit(1)
    except urllib.error.URLError as e:
        print(json.dumps({"error": f"Cannot reach image URL: {e.reason}", "accessible": False}, ensure_ascii=False))
        sys.exit(1)
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {target}", "accessible": False}, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e), "accessible": False}, ensure_ascii=False))
        sys.exit(1)

    fmt = get_image_format(data)
    dims = get_dimensions(data)

    if dims is None:
        result = {
            "accessible": True,
            "format": fmt,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 1),
            "dimensions": None,
            "issues": [{"severity": "WARN", "rule": "W1", "message": f"Could not determine image dimensions (format: {fmt})"}],
            "platform_compatibility": {},
        }
    else:
        width, height = dims
        ratio = width / height if height > 0 else 0
        issues, platform_results = validate_image(width, height, file_size, fmt)
        result = {
            "accessible": True,
            "format": fmt,
            "file_size_bytes": file_size,
            "file_size_kb": round(file_size / 1024, 1),
            "dimensions": {"width": width, "height": height},
            "aspect_ratio": round(ratio, 3),
            "issues": issues,
            "platform_compatibility": platform_results,
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
