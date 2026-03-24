#!/usr/bin/env python3
"""
Fetch a URL and analyze it against Google AdSense approval criteria.
Usage: python3 analyze_page.py <URL>
Output: JSON with analysis results.
"""

import json
import re
import sys
import urllib.request
import urllib.error
import ssl


def fetch(url: str, timeout: int = 10) -> tuple[int, str]:
    """Fetch URL and return (status_code, body)."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; AdSenseChecker/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception as e:
        return 0, str(e)


def strip_tags(html: str) -> str:
    """Remove HTML tags and return visible text."""
    # Remove script and style content
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_meta(html: str, attr: str, name: str) -> str | None:
    """Extract meta tag content by attribute name."""
    pattern = rf'<meta\s+[^>]*{attr}=["\']?{re.escape(name)}["\']?\s+content=["\']([^"\']*)["\']'
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        # Try reversed attribute order
        pattern = rf'<meta\s+[^>]*content=["\']([^"\']*)["\'][\s+[^>]*]*{attr}=["\']?{re.escape(name)}["\']?'
        match = re.search(pattern, html, re.IGNORECASE)
    return match.group(1) if match else None


def extract_title(html: str) -> str:
    """Extract <title> tag content."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def find_links(html: str, base_url: str) -> dict:
    """Extract and categorize links."""
    from urllib.parse import urlparse

    parsed_base = urlparse(base_url)
    base_domain = parsed_base.netloc

    href_pattern = re.compile(r'<a\s+[^>]*href=["\']([^"\'#]+)["\']', re.IGNORECASE)
    all_hrefs = href_pattern.findall(html)

    internal = []
    privacy_found = False

    for href in all_hrefs:
        href_lower = href.lower()

        # Check privacy link
        if any(kw in href_lower for kw in ["privacy", "terms", "policy"]):
            privacy_found = True

        # Check internal link
        if href.startswith("/"):
            if href != "/":
                internal.append(href)
        elif base_domain in href:
            internal.append(href)

    # Also check link text for privacy
    privacy_text_pattern = re.compile(
        r"<a\s+[^>]*>[^<]*(개인정보|이용약관|privacy|terms)[^<]*</a>",
        re.IGNORECASE,
    )
    if privacy_text_pattern.search(html):
        privacy_found = True

    return {
        "internal_link_count": len(set(internal)),
        "internal_links": sorted(set(internal))[:20],
        "has_privacy_link": privacy_found,
    }


def check_placeholders(text: str) -> list[str]:
    """Detect placeholder/dummy content."""
    lower = text.lower()
    found = []
    patterns = [
        ("lorem ipsum", "Lorem ipsum placeholder text"),
        ("placeholder", "Placeholder text detected"),
        ("coming soon", "Coming soon page"),
        ("under construction", "Under construction page"),
        ("example.com", "Example domain reference"),
        ("todo", "TODO marker found"),
    ]
    for pattern, label in patterns:
        if pattern in lower:
            found.append(label)
    return found


def check_nav_elements(html: str) -> dict:
    """Check for navigation-related HTML elements."""
    return {
        "has_nav": bool(re.search(r"<nav[\s>]", html, re.IGNORECASE)),
        "has_header": bool(re.search(r"<header[\s>]", html, re.IGNORECASE)),
        "has_footer": bool(re.search(r"<footer[\s>]", html, re.IGNORECASE)),
    }


def analyze_url(url: str) -> dict:
    """Analyze a single URL for AdSense criteria."""
    status, html = fetch(url)

    if status != 200:
        return {
            "url": url,
            "status": status,
            "error": f"HTTP {status}",
            "checks": {},
        }

    text = strip_tags(html)
    text_no_spaces = re.sub(r"\s+", "", text)
    title = extract_title(html)
    description = extract_meta(html, "name", "description")
    viewport = extract_meta(html, "name", "viewport")
    links = find_links(html, url)
    nav = check_nav_elements(html)
    placeholders = check_placeholders(text)

    # Count empty sections
    section_pattern = re.compile(
        r"<(section|main|article)[^>]*>(.*?)</\1>", re.DOTALL | re.IGNORECASE
    )
    empty_sections = 0
    for match in section_pattern.finditer(html):
        section_text = strip_tags(match.group(2))
        if len(section_text.strip()) < 10:
            empty_sections += 1

    checks = {
        "content": {
            "text_length": len(text_no_spaces),
            "pass": len(text_no_spaces) >= 200,
            "detail": f"{len(text_no_spaces)} chars (min 200)",
        },
        "title": {
            "value": title,
            "pass": len(title) > 0 and "Create Next App" not in title,
            "detail": title if title else "MISSING",
        },
        "meta_description": {
            "value": description,
            "pass": description is not None and len(description) >= 30,
            "detail": (
                f"{len(description)} chars"
                if description
                else "MISSING"
            ),
        },
        "viewport": {
            "value": viewport,
            "pass": viewport is not None and "width=device-width" in (viewport or ""),
            "detail": viewport if viewport else "MISSING",
        },
        "internal_links": {
            "count": links["internal_link_count"],
            "pass": links["internal_link_count"] >= 3,
            "detail": f"{links['internal_link_count']} links found",
            "links": links["internal_links"],
        },
        "privacy_link": {
            "pass": links["has_privacy_link"],
            "detail": "Found" if links["has_privacy_link"] else "NOT FOUND",
        },
        "placeholders": {
            "found": placeholders,
            "pass": len(placeholders) == 0,
            "detail": ", ".join(placeholders) if placeholders else "None",
        },
        "empty_sections": {
            "count": empty_sections,
            "pass": empty_sections == 0,
            "detail": f"{empty_sections} empty sections",
        },
        "navigation": {
            "has_nav": nav["has_nav"],
            "has_header": nav["has_header"],
            "has_footer": nav["has_footer"],
            "pass": nav["has_nav"] or nav["has_header"],
            "detail": ", ".join(
                k for k, v in nav.items() if v
            ) or "No nav/header/footer",
        },
        "https": {
            "pass": url.startswith("https://"),
            "detail": "HTTPS" if url.startswith("https://") else "HTTP only",
        },
    }

    return {
        "url": url,
        "status": status,
        "checks": checks,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: analyze_page.py <URL>"}))
        sys.exit(1)

    url = sys.argv[1]

    # If URL doesn't start with http, add https
    if not url.startswith("http"):
        url = "https://" + url

    result = analyze_url(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
