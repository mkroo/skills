---
name: adsense-checker
description: This skill should be used when the user asks to "check AdSense readiness", "AdSense 심사 확인", "AdSense audit", "사이트 AdSense 준비 확인", "광고 심사 준비", "AdSense approval check", or mentions Google AdSense eligibility, ad monetization readiness, or AdSense rejection troubleshooting.
---

# AdSense Readiness Checker

Check if a website meets Google AdSense approval criteria. Fetch the site, analyze content quality, required pages, technical setup, and policy compliance, then generate a structured report with actionable fixes.

## Core Workflow

The user provides a URL (e.g., `https://example.com`). Run all steps against that base URL.

### Step 1: Infrastructure Files

Check the existence and content of critical files using `WebFetch`:

| File | URL | Check |
|------|-----|-------|
| `robots.txt` | `{BASE}/robots.txt` | Exists, does NOT block Googlebot (`Disallow: /`) |
| `ads.txt` | `{BASE}/ads.txt` | Exists (required after AdSense approval, recommended before) |
| `sitemap.xml` | `{BASE}/sitemap.xml` | Exists (helps Googlebot discover pages) |

### Step 2: Homepage Analysis

Fetch the homepage with `WebFetch` and run the analysis script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/adsense-checker/scripts/analyze_page.py "{BASE}/"
```

The script checks:
- **Content length** — minimum 200 characters of text (excluding HTML tags)
- **Meta tags** — `<title>`, `<meta name="description">`, `<meta name="viewport">`
- **Internal links** — at least 3 internal navigation links
- **Privacy link** — link to privacy policy page present on page
- **Placeholder content** — detects "lorem ipsum", "coming soon", "under construction", etc.
- **HTTPS** — site must use HTTPS

If the script is unavailable, perform these checks manually by inspecting the WebFetch output.

### Step 3: Required Pages

AdSense requires trust/legal pages. Check each candidate URL with `WebFetch`:

**Privacy Policy** (required):
- Check: `/privacy`, `/privacy-policy`, `/terms`, `/policy`
- At least one must return 200 with meaningful content (> 500 chars)

**About / Contact** (strongly recommended):
- Check: `/about`, `/contact`, `/support`
- At least one must return 200

If a page doesn't exist at these standard paths, also check the homepage for inline links to these pages at non-standard paths.

### Step 4: Content Quality (Multi-Page)

Discover internal pages from the homepage links, then check 3-5 pages:

For each page:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/adsense-checker/scripts/analyze_page.py "{PAGE_URL}"
```

Validate:
- **Text content** — each page has ≥ 200 characters of unique text
- **No placeholder text** — no "lorem ipsum", "placeholder", "TODO", "example"
- **No empty sections** — no `<section>`, `<main>`, `<article>` with < 10 chars
- **Meta tags** — each page has unique `<title>` and `<meta description>`
- **No duplicate content** — pages have distinct content from each other

### Step 5: Navigation & UX

Check on the homepage:
- **Global navigation** — `<nav>` or `<header>` element exists
- **Footer with legal links** — privacy policy link in footer
- **No intrusive interstitials** — no full-screen popups/overlays on page load
- **Mobile viewport** — `<meta name="viewport" content="width=device-width">` present

### Step 6: Generate Report

Output a structured report using the criteria from `references/adsense-criteria.md`.

#### Report Format

```
## AdSense Readiness Report — {URL}

### Summary
- Total checks: N
- PASS: N | WARN: N | FAIL: N
- Verdict: Ready / Needs Work / Not Ready

### Results

#### 1. Infrastructure
| Check | Status | Detail |
|-------|--------|--------|
| robots.txt | PASS/WARN/FAIL | ... |
| ads.txt | PASS/WARN/FAIL | ... |
| sitemap.xml | PASS/WARN/FAIL | ... |
| HTTPS | PASS/FAIL | ... |

#### 2. Required Pages
| Check | Status | Detail |
|-------|--------|--------|
| Privacy Policy | PASS/FAIL | ... |
| About / Contact | PASS/WARN | ... |

#### 3. Content Quality
| Page | Text Length | Meta Tags | Placeholder | Status |
|------|------------|-----------|-------------|--------|
| / | 250 chars | ✓ | None | PASS |
| ... | ... | ... | ... | ... |

#### 4. Navigation & UX
| Check | Status | Detail |
|-------|--------|--------|
| Global nav | PASS/FAIL | ... |
| Privacy link on page | PASS/FAIL | ... |
| Mobile viewport | PASS/FAIL | ... |
| No intrusive popups | PASS/WARN | ... |

### Action Items (Prioritized)
1. [FAIL] ... — how to fix
2. [WARN] ... — how to fix
```

#### Severity Levels

- **FAIL** — Will likely cause AdSense rejection. Must fix before applying.
- **WARN** — May contribute to rejection. Strongly recommended to fix.
- **PASS** — Meets AdSense requirements.

#### Verdict Logic

- **Not Ready** — Any FAIL in Infrastructure or Required Pages
- **Needs Work** — No infrastructure/page FAILs, but content FAILs or 3+ WARNs
- **Ready** — No FAILs and fewer than 3 WARNs

## Scripts

- **`scripts/analyze_page.py`** — Fetch a URL and analyze for AdSense criteria (content length, meta tags, links, placeholders)

## References

- **`references/adsense-criteria.md`** — Complete AdSense approval criteria and common rejection reasons
