# mkroo/skills

Claude Code plugin — skills와 MCP 서버 모음.

## Installation

```bash
claude plugin add https://github.com/mkroo/skills
```

## Skills

### [og-validator](skills/og-validator/)

OpenGraph 메타 태그 검증. 페이지를 가져와서 OG/Twitter Card 태그를 추출하고 플랫폼별 요구사항(KakaoTalk, Facebook, Twitter/X 등)에 맞는지 검증 리포트를 생성한다.

### [project-namer](skills/project-namer/)

프로젝트 이름 추천 & 검증. 프로젝트 맥락에서 이름 후보를 생성하고, 도메인/GitHub/npm 가용성, 기존 서비스 충돌, 검색 고유성 등 6가지 항목으로 평가하여 총합 추천도를 산출한다.

### [adsense-checker](skills/adsense-checker/)

Google AdSense 심사 준비 확인. URL을 입력하면 콘텐츠 충분성, 필수 페이지, 기술 요구사항, 광고 정책 준수 여부를 검사하고 PASS/WARN/FAIL 리포트를 생성한다.

## MCP Servers

### [gtm-ga4](mcp-servers/gtm-ga4/)

Google Tag Manager + Google Analytics 4 관리. 코드의 이벤트를 분석해서 GTM 변수/트리거/태그 생성, GA4 맞춤 측정기준 등록, 게시까지 대화 한번으로 처리한다. `npm install` 필요 — [설정 가이드](mcp-servers/gtm-ga4/README.md#setup) 참고.

## License

MIT
