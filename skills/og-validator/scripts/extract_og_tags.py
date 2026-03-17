#!/usr/bin/env python3
"""Extract OpenGraph and Twitter Card meta tags from HTML.

Usage:
    python3 extract_og_tags.py "<html>..."          # HTML as argument
    echo "<html>..." | python3 extract_og_tags.py   # HTML from stdin

Output: JSON with extracted tags and basic validation.
"""

import json
import re
import sys
from html.parser import HTMLParser


class OGTagParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og_tags = {}
        self.twitter_tags = {}
        self.other_meta = {}
        self.canonical = None
        self.title_tag = None
        self._in_title = False
        self._title_data = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "title":
            self._in_title = True
            self._title_data = []
            return

        if tag == "link" and attrs_dict.get("rel") == "canonical":
            self.canonical = attrs_dict.get("href", "")
            return

        if tag != "meta":
            return

        prop = attrs_dict.get("property", "")
        name = attrs_dict.get("name", "")
        content = attrs_dict.get("content", "")

        if prop.startswith("og:"):
            key = prop
            if key in self.og_tags:
                if isinstance(self.og_tags[key], list):
                    self.og_tags[key].append(content)
                else:
                    self.og_tags[key] = [self.og_tags[key], content]
            else:
                self.og_tags[key] = content

        elif name.startswith("twitter:") or prop.startswith("twitter:"):
            key = name or prop
            self.twitter_tags[key] = content

        elif name == "description":
            self.other_meta["description"] = content

    def handle_data(self, data):
        if self._in_title:
            self._title_data.append(data)

    def handle_endtag(self, tag):
        if tag == "title" and self._in_title:
            self._in_title = False
            self.title_tag = "".join(self._title_data).strip()


PLACEHOLDER_PATTERNS = [
    r"\{\{.*?\}\}",
    r"\$\{.*?\}",
    r"^undefined$",
    r"^null$",
    r"^\[object Object\]$",
    r"^lorem ipsum",
    r"^TODO",
    r"^Untitled$",
    r"^Home$",
    r"^Welcome to\s*$",
    r"^test$",
    r"^example$",
]


def is_placeholder(text):
    if not text:
        return True
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text.strip(), re.IGNORECASE):
            return True
    return False


def is_absolute_url(url):
    return bool(re.match(r"^https?://", url))


def is_https_url(url):
    return url.startswith("https://")


def is_localhost_url(url):
    return bool(re.search(r"(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?", url))


def validate_tags(parser):
    issues = []

    # Required tags
    if not parser.og_tags.get("og:title"):
        issues.append({"rule": "F1", "severity": "FAIL", "message": "og:title is missing or empty"})
    if not parser.og_tags.get("og:image"):
        issues.append({"rule": "F2", "severity": "FAIL", "message": "og:image is missing"})
    if not parser.og_tags.get("og:url"):
        issues.append({"rule": "F5", "severity": "FAIL", "message": "og:url is missing"})

    # Duplicate tags
    for key, value in parser.og_tags.items():
        if isinstance(value, list):
            issues.append({"rule": "F6", "severity": "FAIL", "message": f"Duplicate {key} tags found ({len(value)} instances)"})

    # Image URL checks
    og_image = parser.og_tags.get("og:image", "")
    if isinstance(og_image, list):
        og_image = og_image[0]
    if og_image:
        if not is_absolute_url(og_image):
            issues.append({"rule": "F4", "severity": "FAIL", "message": f"og:image uses relative URL: {og_image}"})
        elif not is_https_url(og_image) and not is_localhost_url(og_image):
            issues.append({"rule": "F7", "severity": "FAIL", "message": f"og:image uses HTTP instead of HTTPS: {og_image}"})

        if is_localhost_url(og_image):
            issues.append({"rule": "W14", "severity": "WARN", "message": f"og:image uses localhost URL (won't work in production): {og_image}"})

    # og:url checks
    og_url = parser.og_tags.get("og:url", "")
    if og_url:
        if not is_absolute_url(og_url):
            issues.append({"rule": "F4", "severity": "FAIL", "message": f"og:url uses relative URL: {og_url}"})
        if is_localhost_url(og_url):
            issues.append({"rule": "W14", "severity": "WARN", "message": f"og:url uses localhost URL (won't work in production): {og_url}"})
        if parser.canonical and og_url != parser.canonical:
            issues.append({"rule": "W11", "severity": "WARN", "message": f"og:url ({og_url}) doesn't match canonical ({parser.canonical})"})

    # Text quality
    og_title = parser.og_tags.get("og:title", "")
    if isinstance(og_title, list):
        og_title = og_title[0]
    if og_title:
        if is_placeholder(og_title):
            issues.append({"rule": "W15", "severity": "WARN", "message": f"og:title appears to be placeholder text: {og_title}"})
        title_len = len(og_title)
        if title_len < 15:
            issues.append({"rule": "W4", "severity": "WARN", "message": f"og:title too short ({title_len} chars), recommend 30-60"})
        elif title_len > 70:
            issues.append({"rule": "W4", "severity": "WARN", "message": f"og:title too long ({title_len} chars), may be truncated on Twitter (>70)"})

    og_desc = parser.og_tags.get("og:description", "")
    if not og_desc:
        issues.append({"rule": "W6", "severity": "WARN", "message": "og:description is missing"})
    else:
        if is_placeholder(og_desc):
            issues.append({"rule": "W15", "severity": "WARN", "message": f"og:description appears to be placeholder text: {og_desc}"})
        desc_len = len(og_desc)
        if desc_len < 30:
            issues.append({"rule": "W5", "severity": "WARN", "message": f"og:description too short ({desc_len} chars), recommend 65-155"})
        elif desc_len > 200:
            issues.append({"rule": "W5", "severity": "WARN", "message": f"og:description too long ({desc_len} chars), may be truncated on some platforms"})

    if og_title and og_desc and og_title.strip() == og_desc.strip():
        issues.append({"rule": "W15", "severity": "WARN", "message": "og:title and og:description are identical"})

    # Optional but recommended tags
    if not parser.og_tags.get("og:type"):
        issues.append({"rule": "W7", "severity": "WARN", "message": "og:type is missing (defaults to 'website')"})
    if not parser.og_tags.get("og:image:alt") and og_image:
        issues.append({"rule": "W8", "severity": "WARN", "message": "og:image:alt is missing (accessibility concern)"})
    if not parser.og_tags.get("og:locale"):
        issues.append({"rule": "W9", "severity": "WARN", "message": "og:locale is missing (e.g., ko_KR for Korean content)"})
    if not parser.og_tags.get("og:site_name"):
        issues.append({"rule": "W12", "severity": "WARN", "message": "og:site_name is missing"})
    if not parser.og_tags.get("og:image:width") or not parser.og_tags.get("og:image:height"):
        issues.append({"rule": "W13", "severity": "WARN", "message": "og:image:width/height missing (crawlers may need extra fetch)"})

    # Twitter Card
    if not parser.twitter_tags.get("twitter:card"):
        issues.append({"rule": "W10", "severity": "WARN", "message": "twitter:card is missing (Twitter won't show large image preview)"})

    # Title repeats site name
    site_name = parser.og_tags.get("og:site_name", "")
    if og_title and site_name and og_title.strip() == site_name.strip():
        issues.append({"rule": "W16", "severity": "WARN", "message": "og:title is identical to og:site_name"})

    return issues


def main():
    if len(sys.argv) > 1:
        html = sys.argv[1]
    else:
        html = sys.stdin.read()

    if not html.strip():
        print(json.dumps({"error": "No HTML input provided"}, ensure_ascii=False))
        sys.exit(1)

    parser = OGTagParser()
    parser.feed(html)

    issues = validate_tags(parser)

    result = {
        "og_tags": {k: v for k, v in parser.og_tags.items()},
        "twitter_tags": parser.twitter_tags,
        "canonical": parser.canonical,
        "html_title": parser.title_tag,
        "meta_description": parser.other_meta.get("description"),
        "issues": issues,
        "summary": {
            "total_og_tags": len(parser.og_tags),
            "total_twitter_tags": len(parser.twitter_tags),
            "fail_count": sum(1 for i in issues if i["severity"] == "FAIL"),
            "warn_count": sum(1 for i in issues if i["severity"] == "WARN"),
        },
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
