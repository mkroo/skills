# Platform-Specific OpenGraph Specifications

## Required OG Tags (per ogp.me protocol)

| Tag | Required | Description |
|-----|----------|-------------|
| `og:title` | Yes | Page title for social preview |
| `og:type` | Yes | Content type: `website`, `article`, `product`, etc. |
| `og:image` | Yes | Preview image URL (absolute, HTTPS) |
| `og:url` | Yes | Canonical page URL (absolute) |

## Strongly Recommended Tags

| Tag | Description |
|-----|-------------|
| `og:description` | 1-2 sentence summary |
| `og:image:width` | Image width in pixels (helps crawlers) |
| `og:image:height` | Image height in pixels (helps crawlers) |
| `og:image:alt` | Alt text for accessibility |
| `og:site_name` | Overall site name |
| `og:locale` | Language/country code (e.g., `ko_KR`, `en_US`) |

## Twitter Card Tags

| Tag | Description |
|-----|-------------|
| `twitter:card` | Card type: `summary_large_image` recommended |
| `twitter:title` | Falls back to `og:title` if absent |
| `twitter:description` | Falls back to `og:description` if absent |
| `twitter:image` | Falls back to `og:image` if absent |
| `twitter:image:alt` | Image alt text |

---

## Image Requirements by Platform

| Platform | Recommended Size | Min Size | Aspect Ratio | Max File Size | Format |
|----------|-----------------|----------|--------------|---------------|--------|
| KakaoTalk | 800x400 or 1200x630 | 80x80 | 2:1 preferred | 500KB | JPG, PNG |
| Facebook | 1200x630 | 600x315 | 1.91:1 | 8MB | JPG, PNG, WebP, GIF |
| Twitter/X | 1200x628 | 400x400 | 2:1 | 5MB | JPG, PNG, GIF |
| Discord | 1200x630 | 400x300 | 1.91:1 | 8MB | JPG, PNG, GIF |
| Slack | 1200x630 | 400x400 | 1.91:1 | - | JPG, PNG |
| LinkedIn | 1200x627 | 200x200 | 1.91:1 | 5MB | JPG, PNG |
| WhatsApp | 1200x630 | 300x200 | 1.91:1 | 200KB preferred | JPG, PNG |
| LINE | 1200x630 | - | 1.91:1 | - | JPG, PNG |

### Universal Safe Zone

- **Dimensions**: 1200x630 pixels (works across all platforms)
- **File size**: ≤500KB (satisfies KakaoTalk's strict limit)
- **Safe area**: Keep critical content (text, logos) within the center 80% of the image
- **Format**: JPG for photos, PNG for graphics with text

---

## Text Length Limits by Platform

### og:title

| Platform | Ideal Length | Truncation Point |
|----------|-------------|------------------|
| KakaoTalk | ~30 chars (Korean) | Varies by UI |
| Facebook | 40-60 chars | ~88 chars |
| Twitter/X | ~70 chars | 70 chars |
| Discord | ~60 chars | ~256 chars |
| Slack | ~60 chars | Varies |
| LinkedIn | ~60 chars | ~200 chars |

### og:description

| Platform | Ideal Length | Truncation Point |
|----------|-------------|------------------|
| KakaoTalk | ~50 chars (Korean) | Varies by UI |
| Facebook | 150-200 chars | ~300 chars |
| Twitter/X | ~150 chars | 200 chars |
| Discord | ~150 chars | ~350 chars |
| Slack | ~150 chars | Varies |
| LinkedIn | ~100 chars | ~300 chars |

### Character Counting Notes

- Korean/CJK characters are visually wider — target roughly half the English character counts
- Emoji count as 1-2 characters but take more visual space
- Always test actual rendering, not just character count

---

## Validation Rules

### FAIL (broken or missing preview)

| # | Rule | Description |
|---|------|-------------|
| F1 | `og:title` missing or empty | No title in preview |
| F2 | `og:image` missing | No image in preview |
| F3 | `og:image` not accessible | Image URL returns non-200 or requires auth |
| F4 | `og:image` uses relative URL | Crawlers cannot resolve relative paths |
| F5 | `og:url` missing | Platform cannot determine canonical page |
| F6 | Duplicate OG tags | Unpredictable behavior across platforms |
| F7 | `og:image` uses HTTP (not HTTPS) | Twitter will not display; others may block |

### WARN (degraded preview on some platforms)

| # | Rule | Description |
|---|------|-------------|
| W1 | Image < 1200x630 | May appear small or blurry |
| W2 | Image > 500KB | KakaoTalk may not display; WhatsApp slow |
| W3 | Image aspect ratio not ~1.91:1 | Will be cropped differently per platform |
| W4 | `og:title` too short (< 15 chars) or too long (> 70 chars) | Poor readability or truncation |
| W5 | `og:description` too short (< 30 chars) or too long (> 200 chars) | Insufficient context or truncation |
| W6 | `og:description` missing | Some platforms show blank description |
| W7 | `og:type` missing | Defaults to `website`, may affect rich display |
| W8 | `og:image:alt` missing | Accessibility concern |
| W9 | `og:locale` missing | May default incorrectly for non-English content |
| W10 | `twitter:card` missing | Twitter won't show large image preview |
| W11 | `og:url` doesn't match canonical | May cause preview/SEO mismatch |
| W12 | `og:site_name` missing | Some platforms show blank site name |
| W13 | `og:image:width`/`og:image:height` missing | Crawlers may need extra fetch to determine size |
| W14 | Localhost URL in `og:url` or `og:image` | Will not work in production |
| W15 | Title or description is placeholder text | `{{title}}`, `undefined`, `null`, `lorem ipsum`, etc. |
| W16 | Title repeats site name | Redundant when `og:site_name` is set |
| W17 | Critical image content outside center 80% | May be cropped on some platforms |

---

## Text Quality Detection

### Placeholder Patterns (FAIL/WARN)

Detect these patterns in `og:title` and `og:description`:

```
{{...}}          — Template variable not rendered
${...}           — Template literal not rendered
undefined        — JavaScript undefined leaked
null             — Null value leaked
[object Object]  — JS object serialization leak
Lorem ipsum      — Placeholder text
TODO             — Unfinished content
Untitled         — Default/generic title
Home             — Too generic (title only)
Welcome to       — Too generic without specifics
```

### Contextual Quality (WARN)

- Title and description should not be identical
- Description should not just repeat the title with minor changes
- Title should convey the specific content, not just the site name
- For article-type content, description should hint at the article's value proposition

---

## Cache Clearing Tools

After fixing OG tags, clear platform caches to see updated previews:

| Platform | Tool | URL |
|----------|------|-----|
| KakaoTalk | OG Cache Clear | https://developers.kakao.com/tool/clear/og |
| Facebook | Sharing Debugger | https://developers.facebook.com/tools/debug/ |
| Twitter/X | Card Validator | https://cards-dev.twitter.com/validator |
| LinkedIn | Post Inspector | https://www.linkedin.com/post-inspector/ |

---

## Report Format

Generate the report in the following structure:

```
## OG Validation Report: {URL}

### Detected Tags

| Tag | Value | Status |
|-----|-------|--------|
| og:title | "..." | PASS/WARN/FAIL |
| og:description | "..." | PASS/WARN/FAIL |
| ... | ... | ... |

### Image Analysis

- URL: ...
- Accessible: Yes/No
- Dimensions: WxH
- File size: ...KB
- Aspect ratio: ...
- Format: ...

### Platform Preview Simulation

#### KakaoTalk
┌─────────────────────────────────┐
│ [Image 1200x630]                │
├─────────────────────────────────┤
│ {og:title, truncated to ~30ch}  │
│ {og:description, truncated}     │
│ {domain}                        │
└─────────────────────────────────┘

#### Facebook
┌─────────────────────────────────┐
│ [Image 1200x630]                │
├─────────────────────────────────┤
│ {domain}                        │
│ {og:title, truncated to ~60ch}  │
│ {og:description, truncated}     │
└─────────────────────────────────┘

#### Twitter/X
┌─────────────────────────────────┐
│ [Image 1200x628]                │
│                    {domain} ──┘ │
├─────────────────────────────────┤
│ {og:title, truncated to ~70ch}  │
│ {og:description, truncated}     │
└─────────────────────────────────┘

### Validation Results

#### FAIL
- [F1] og:image uses relative URL `/images/og.png`
  → Change to absolute HTTPS URL

#### WARN
- [W2] Image file size 1.2MB exceeds 500KB
  → Compress to ≤500KB for KakaoTalk compatibility

#### PASS
- [✓] og:title present (45 chars)
- [✓] og:description present (120 chars)
- ...

### Suggested Fixes

1. **[F1] Fix og:image URL**
   ```html
   <!-- Before -->
   <meta property="og:image" content="/images/og.png">
   <!-- After -->
   <meta property="og:image" content="https://example.com/images/og.png">
   ```

2. **[W2] Compress image**
   Reduce file size from 1.2MB to ≤500KB.
   Tools: squoosh.app, tinypng.com, or `sharp` library.

### Cache Clearing Reminders

After applying fixes, clear caches:
- KakaoTalk: https://developers.kakao.com/tool/clear/og
- Facebook: https://developers.facebook.com/tools/debug/
```
