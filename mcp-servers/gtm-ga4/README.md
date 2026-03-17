# GTM + GA4 MCP Server

Google Tag Manager와 Google Analytics 4를 Claude Code에서 직접 관리할 수 있는 MCP 서버.

## Why?

GTM 설정은 반복적이고 실수하기 쉽다.

- 데이터 영역 변수 20개를 콘솔에서 하나씩 만드는 건 비효율적
- 코드에서 보내는 이벤트와 GTM 설정이 싱크가 안 맞으면 데이터 유실
- 새 프로젝트마다 같은 작업을 반복해야 함

이 MCP를 사용하면 Claude가 코드베이스의 이벤트를 분석하고, GTM/GA4 설정을 자동으로 생성하고, 게시까지 한번에 처리한다.

```
"코드에서 보내는 이벤트 분석해서 GTM 설정해줘"
```

이 한마디로 끝.

## Tools

### GTM

| Tool | 설명 |
|------|------|
| `gtm_list_accounts` | GTM 계정 목록 조회 |
| `gtm_list_containers` | 컨테이너 목록 조회 |
| `gtm_list_workspaces` | 워크스페이스 목록 조회 |
| `gtm_create_workspace` | 새 워크스페이스 생성 |
| `gtm_list_variables` | 변수 목록 조회 |
| `gtm_create_datalayer_variables` | 데이터 영역 변수 배치 생성 |
| `gtm_list_triggers` | 트리거 목록 조회 |
| `gtm_create_custom_event_trigger` | 맞춤 이벤트 트리거 생성 (정규식 지원) |
| `gtm_list_tags` | 태그 목록 조회 |
| `gtm_create_google_tag` | Google Tag (GA4 설정) 생성 |
| `gtm_create_ga4_event_tag` | GA4 이벤트 태그 생성 |
| `gtm_publish` | 워크스페이스 버전 생성 + 게시 |

### GA4

| Tool | 설명 |
|------|------|
| `ga4_list_properties` | GA4 속성 목록 조회 |
| `ga4_list_custom_dimensions` | 맞춤 측정기준 목록 조회 |
| `ga4_create_custom_dimensions` | 맞춤 측정기준 배치 생성 |

## Setup

### 1. GCP API 활성화

[Google Cloud Console](https://console.cloud.google.com/apis/library)에서 두 API를 활성화한다:

- **Tag Manager API**
- **Google Analytics Admin API**

### 2. 서비스 계정 생성

1. GCP Console → IAM → 서비스 계정 → 만들기
2. JSON 키 다운로드
3. 안전한 경로에 저장 (예: `~/.config/gcloud/gtm-sa-key.json`)

### 3. 권한 부여

**GTM:**
- [tagmanager.google.com](https://tagmanager.google.com) → 컨테이너 설정 → 사용자 관리
- 서비스 계정 이메일 추가 → **편집** 권한

**GA4:**
- [analytics.google.com](https://analytics.google.com) → 관리 → 속성 액세스 관리
- 서비스 계정 이메일 추가 → **편집자** 역할

### 4. 환경변수 설정

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/.config/gcloud/gtm-sa-key.json"
```

셸 프로필(`~/.zshrc` 등)에 추가하면 영구 적용.

### 5. 의존성 설치

```bash
cd mcp-servers/gtm-ga4 && npm install
```

## Usage Examples

### 전체 GTM 설정 자동화

```
코드에서 dataLayer.push로 보내는 이벤트 전부 분석해서
GTM에 변수, 트리거, 태그 만들고 게시해줘.
GA4 ID는 G-XXXXXXXX이야.
```

Claude가 수행하는 작업:
1. `gtm_list_accounts` → 계정/컨테이너 탐색
2. `gtm_create_workspace` → 작업용 워크스페이스 생성
3. `gtm_create_datalayer_variables` → 코드의 파라미터에 대응하는 변수 배치 생성
4. `gtm_create_custom_event_trigger` → 포괄 이벤트 트리거 생성
5. `gtm_create_google_tag` → GA4 설정 태그 생성
6. `gtm_create_ga4_event_tag` → 이벤트 포워딩 태그 생성
7. `gtm_publish` → 게시

### GA4 맞춤 측정기준 등록

```
코드에서 사용하는 이벤트 파라미터를 GA4 맞춤 측정기준으로 등록해줘.
```

### 현재 설정 확인

```
GTM 컨테이너에 어떤 태그랑 트리거가 있는지 확인해줘.
```
