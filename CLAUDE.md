# mkroo/skills

Claude Code 플러그인 — skills와 MCP 서버 모음.

## 컴포넌트 추가 규칙

### Skill 추가 시

1. `skills/<skill-name>/` 디렉토리 생성
2. `SKILL.md`에 프론트매터(name, description) + 사용법 작성
3. 디렉토리 하위에 **README 또는 SKILL.md**에 이 skill이 **해결하고자 하는 문제**가 무엇인지 명확히 기술
4. 루트 `README.md`의 Skills 섹션에 한줄 요약 + 디렉토리 링크 추가

### MCP Server 추가 시

1. `mcp-servers/<server-name>/` 디렉토리 생성
2. `src/index.ts` + `package.json` + `tsconfig.json` 구성
3. `.claude-plugin/plugin.json`의 `mcpServers`에 서버 등록
4. 디렉토리 하위에 **README.md**에 다음 내용 필수 기재:
   - 이 MCP가 **해결하고자 하는 문제** (Why?)
   - 제공하는 **도구 목록**
   - **설치/설정 방법** (API 활성화, 인증, 환경변수 등)
   - **사용 예시**
5. 루트 `README.md`의 MCP Servers 섹션에 한줄 요약 + 디렉토리 링크 추가

### 공통

- 각 컴포넌트의 상세 문서는 해당 디렉토리 하위에 둔다
- 루트 README는 인덱스 역할만 한다 — 각 항목의 한줄 요약과 링크만 포함
