---
name: og-validator
description: This skill should be used when the user asks to "validate OpenGraph tags", "check OG tags", "preview OG image", "check social sharing preview", "OG 확인", "오픈그래프 검증", "카카오톡 미리보기 확인", "og:image check", or mentions OpenGraph validation, social link preview debugging, or OG meta tag issues.
---

# OpenGraph Validator

Validate OpenGraph meta tags and preview images for social sharing platforms. Fetch a page from localhost or any URL, extract all OG/Twitter Card meta tags, validate against platform-specific requirements, and generate a comprehensive report.

## Core Workflow

### Step 1: Fetch the Page

Use `WebFetch` to retrieve the full HTML from the target URL. For localhost development servers, confirm the dev server is running before fetching.

```
WebFetch → target URL → raw HTML
```

### Step 2: Extract OG Tags

Run the extraction script to parse all OG and Twitter Card meta tags from the HTML:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/og-validator/scripts/extract_og_tags.py "<html>..."
```

The script outputs structured JSON with all detected meta tags, their values, and basic validation flags.

If the script is unavailable, parse the HTML directly by searching for `<meta property="og:..."` and `<meta name="twitter:..."` patterns.

### Step 3: Validate Tags

Check all extracted tags against the rules in `references/platform-specs.md`. Key validation categories:

#### Required Tags
- `og:title` — present, non-empty, not a placeholder
- `og:type` — present (`website`, `article`, etc.)
- `og:image` — present, absolute HTTPS URL
- `og:url` — present, absolute URL, matches canonical

#### Image Validation
- Fetch the `og:image` URL with `WebFetch` to confirm accessibility
- Run the image analysis script for dimension/size checks:
  ```bash
  python3 ${CLAUDE_PLUGIN_ROOT}/skills/og-validator/scripts/check_image.py "<image_url_or_path>"
  ```
- Verify: dimensions (min 1200x630 recommended), aspect ratio (~1.91:1), file size (≤500KB for KakaoTalk compatibility)
- Check that the image URL does not require authentication or cookies

#### Text Quality
- `og:title`: 30-60 characters ideal, detect placeholders (`{{title}}`, `undefined`, `null`, default framework text)
- `og:description`: 65-155 characters ideal, meaningful content (not lorem ipsum, not repeating the title)
- Assess whether title and description provide enough context for a viewer to understand the shared content

#### Technical Checks
- All URLs are absolute (not relative paths)
- `og:url` matches `<link rel="canonical">` if present
- No duplicate OG tags
- HTTPS enforced for `og:image` (required by Twitter, recommended everywhere)
- `og:image:alt` present when `og:image` exists
- `og:locale` set (e.g., `ko_KR` for Korean content)
- Twitter Card tags present (`twitter:card` at minimum)

### Step 4: Generate Report

Output a structured validation report. Use the format from `references/platform-specs.md` section "Report Format".

Report sections:
1. **Tag Overview** — all detected OG/Twitter tags with values
2. **Validation Results** — per-check pass/warn/fail with reasons
3. **Platform Preview** — text-based simulation for KakaoTalk, Facebook, Twitter
4. **Action Items** — prioritized list of fixes with code examples

Severity levels:
- **FAIL**: Will cause broken or missing previews (missing required tags, inaccessible image, relative URLs)
- **WARN**: May cause degraded previews on some platforms (suboptimal image size, missing optional tags, text too long/short)
- **PASS**: Meets requirements

### Step 5: Suggest Fixes

For each FAIL/WARN item, provide a concrete code fix. Example:

```html
<!-- Before -->
<meta property="og:image" content="/images/og.png">

<!-- After -->
<meta property="og:image" content="https://example.com/images/og.png">
```

## Platform-Specific Details

For detailed platform specs (image dimensions, text limits, cache clearing tools), consult:
- **`references/platform-specs.md`** — Complete platform requirements and validation rules

## Scripts

- **`scripts/extract_og_tags.py`** — Extract and structure OG tags from raw HTML (stdin or argument)
- **`scripts/check_image.py`** — Download image and validate dimensions, file size, format

## Localhost Development Notes

- When validating localhost URLs, `og:url` and `og:image` may legitimately use `localhost`. Flag this as a **WARN** — remind the user these must be absolute public URLs in production.
- For `og:image` pointing to localhost, still fetch and validate the image dimensions/format.
- Suggest the user check platform-specific cache clearing tools after deploying fixes (links in `references/platform-specs.md`).
