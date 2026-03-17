# mkroo/skills

A collection of personal development skills for Claude Code.

## Installation

```bash
claude plugin add https://github.com/mkroo/skills
```

## Skills

### og-validator

Validate OpenGraph meta tags and preview images for social sharing platforms.

- Fetches your page (including localhost dev servers), extracts all OG/Twitter Card tags
- Validates against platform-specific requirements (KakaoTalk, Facebook, Twitter/X, Discord, Slack, LinkedIn, WhatsApp)
- Generates a structured report with fix suggestions

**Usage:**

```
> Check the OG tags on http://localhost:3000/blog/my-post
> 이 페이지 OG 확인해줘 http://localhost:3000
> Validate OpenGraph for http://localhost:5173/about
```

For full details, see [skills/og-validator/SKILL.md](skills/og-validator/SKILL.md).

## Project Structure

```
skills/
├── .claude-plugin/
│   ├── plugin.json              # Plugin metadata (mkroo-skills)
│   └── marketplace.json         # Marketplace registry
├── skills/
│   └── og-validator/            # OpenGraph validator skill
│       ├── SKILL.md
│       ├── references/
│       │   └── platform-specs.md
│       └── scripts/
│           ├── extract_og_tags.py
│           └── check_image.py
├── LICENSE
├── .gitignore
└── README.md
```

## Adding a New Skill

1. Create a new directory under `skills/`:
   ```
   skills/my-new-skill/
   └── SKILL.md
   ```
2. The skill will be auto-discovered by Claude Code via the `skills/` directory convention.

## License

MIT
