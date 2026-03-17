# og-validator-skill

A Claude Code skill that validates OpenGraph meta tags for social sharing previews.

Fetches your page (including localhost dev servers), extracts all OG/Twitter Card tags, validates against platform-specific requirements, and generates a report with fix suggestions.

## Problems This Solves

- Images not showing or cropped on KakaoTalk, Facebook, Twitter
- Title/description too short, too generic, or showing placeholder text
- Relative URLs, missing HTTPS, duplicate tags
- Missing accessibility tags (`og:image:alt`)

## Validated Platforms

| Platform | Image | Title | Description |
|----------|-------|-------|-------------|
| KakaoTalk | 800x400, ≤500KB, 2:1 | ~30 chars (KR) | ~50 chars (KR) |
| Facebook | 1200x630, ≤8MB, 1.91:1 | 40-60 chars | 150-200 chars |
| Twitter/X | 1200x628, ≤5MB, 2:1 | ~70 chars | ~200 chars |
| Discord | 1200x630, ≤8MB, 1.91:1 | ~60 chars | ~150 chars |
| Slack | 1200x630, 1.91:1 | ~60 chars | ~150 chars |
| LinkedIn | 1200x627, ≤5MB, 1.91:1 | ~60 chars | ~100 chars |
| WhatsApp | 1200x630, ≤200KB, 1.91:1 | - | - |

## Installation

```bash
# Install as a Claude Code plugin
claude plugin add /path/to/og-validator-skill

# Or clone and use --plugin-dir
git clone https://github.com/ansrl/og-validator-skill.git
claude --plugin-dir ./og-validator-skill
```

## Usage

The skill auto-triggers when you mention OpenGraph, OG tags, or social sharing previews:

```
> Check the OG tags on http://localhost:3000/blog/my-post

> 이 페이지 OG 확인해줘 http://localhost:3000

> Validate OpenGraph for http://localhost:5173/about
```

### What It Checks

**Required Tags** — `og:title`, `og:type`, `og:image`, `og:url`

**Image Validation**
- Accessible (no auth/cookies required)
- Dimensions (min 1200x630 recommended)
- File size (≤500KB for KakaoTalk)
- Aspect ratio (~1.91:1 to 2:1)
- Absolute HTTPS URL

**Text Quality**
- Length within platform limits
- Not placeholder text (`{{title}}`, `undefined`, `null`)
- Title ≠ description, meaningful content

**Technical**
- Absolute URLs (not relative)
- `og:url` matches `<link rel="canonical">`
- No duplicate tags
- `og:image:alt` for accessibility
- `twitter:card` for Twitter previews

### Report Output

The skill generates a structured report including:
1. All detected OG/Twitter tags
2. Image analysis (dimensions, file size, format)
3. Text-based platform preview simulation (KakaoTalk, Facebook, Twitter)
4. Prioritized FAIL/WARN/PASS results
5. Concrete code fixes for each issue

## Project Structure

```
og-validator-skill/
├── .claude-plugin/
│   ├── plugin.json            # Plugin metadata
│   └── marketplace.json       # Marketplace registry
├── skills/
│   └── og-validator/
│       ├── SKILL.md           # Core workflow (~1,500 words)
│       ├── references/
│       │   └── platform-specs.md   # Platform requirements & report format
│       └── scripts/
│           ├── extract_og_tags.py  # HTML → structured OG data
│           └── check_image.py      # Image dimension/size validation
├── LICENSE                    # MIT
├── .gitignore
└── README.md
```

## Scripts

Both scripts use Python stdlib only (no pip install needed).

### extract_og_tags.py

Extracts OG and Twitter Card meta tags from HTML:

```bash
# From argument
python3 scripts/extract_og_tags.py '<html><head><meta property="og:title" content="Test">...</head></html>'

# From stdin
curl -s http://localhost:3000 | python3 scripts/extract_og_tags.py
```

### check_image.py

Validates image dimensions, file size, and format:

```bash
# From URL
python3 scripts/check_image.py https://example.com/og-image.png

# From local file
python3 scripts/check_image.py ./public/og-image.png
```

## Cache Clearing

After fixing OG tags, clear platform caches:

| Platform | Tool |
|----------|------|
| KakaoTalk | https://developers.kakao.com/tool/clear/og |
| Facebook | https://developers.facebook.com/tools/debug/ |
| Twitter/X | https://cards-dev.twitter.com/validator |
| LinkedIn | https://www.linkedin.com/post-inspector/ |

## License

MIT
