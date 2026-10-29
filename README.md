# BMS 데모 시스템

- 📄 소개 페이지 (한국어/English): https://ykn9080.github.io/bms/
- 🌐 데모 사이트: https://yknam.duckdns.org

Docker Compose 기반의 BMS(건물 관리 시스템) 데모 시스템입니다. 가상 센서 데이터를 생성하고, 이를 시계열 DB와 관계형 DB에 나누어 저장한 뒤 Grafana 대시보드로 시각화합니다.

## 주요 기능

- **가상 센서 데이터 생성**: BMS 센서/장비 데이터를 가상으로 생성
- **백엔드 프로세스 처리**: Node-RED로 데이터 수집 및 처리 흐름 구성
- **데이터 이원화 저장**
  - InfluxDB: IoT 시계열 데이터 전체 저장
  - PostgreSQL: 비정상 데이터만 선별 저장
- **대시보드**: Grafana로 차트 및 데모 화면 제공
- **외부 공개 구조**: Nginx 리버스 프록시를 통해서만 외부에 노출

## 시스템 구성

```
[사용자 브라우저]
       │ HTTPS (443)
       ▼
[Nginx] ─ reverse proxy ─▶ [Grafana] ── 쿼리 ──▶ [InfluxDB]
                                   └────── 쿼리 ──▶ [PostgreSQL]
[BMS 센서/장비 (가상데이터 생성)]
       │
       ▼
[Node-RED] 백엔드 프로세스 엔진
       ├─▶ [InfluxDB]    (IoT 시계열 데이터 전체)
       └─▶ [PostgreSQL]  (비정상 데이터만 선별 저장)
```

### 서비스 구성

| 서비스 | 이미지 | 역할 | 외부 노출 |
|---|---|---|---|
| nginx | `nginx:alpine` | Reverse proxy, HTTPS 종단 | 80, 443 |
| grafana | `grafana/grafana:11.5.2` | 차트 및 데모 시스템 | 없음 (내부) |
| node-red | `nodered/node-red:latest` | 백엔드 프로세스 엔진 | 없음 (내부) |
| influxdb | `influxdb:2.7-alpine` | IoT용 시계열 DB | 없음 (내부) |
| postgres | `postgres:15-alpine` | 비정상 데이터 저장 DB | 없음 (내부) |

모든 서비스는 `iot-network` 브리지 네트워크에서 동작하며, Nginx를 제외한 서비스는 `127.0.0.1`에만 바인딩됩니다.

## 디렉터리 구조

<!-- 실제 구조에 맞게 수정하세요 -->
```
.
├── docker-compose.yml
├── nginx.conf
├── .env                # 민감 정보 (Git에 올리지 않음)
├── .env.example
├── nodered_data/       # Node-RED flows.json, package.json
├── grafana_data/
├── influxdb_data/
├── influxdb_config/
└── postgres_data/
```

## 사전 준비

- Docker 및 Docker Compose
- 도메인 (데모에서는 DuckDNS 사용)
- HTTPS 인증서 (Let's Encrypt, `/etc/letsencrypt` 경로에 발급)

## 설치 및 실행

1. 저장소 클론

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. 환경변수 파일 준비

   ```bash
   cp .env.example .env
   # .env 파일을 열어 실제 값으로 수정
   ```

3. 컨테이너 실행

   ```bash
   docker compose up -d
   ```

4. 상태 확인

   ```bash
   docker compose ps
   docker compose logs -f
   ```

## 환경변수 (.env)

`.env.example`에 아래 항목을 정의하세요.

```env
# PostgreSQL
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# InfluxDB
INFLUXDB_ADMIN_USER=
INFLUXDB_ADMIN_PASSWORD=
INFLUXDB_ORGANIZATION=
INFLUXDB_BUCKET_NAME=
INFLUXDB_ADMIN_TOKEN=

# Grafana
GF_SECURITY_ADMIN_USER=
GF_SECURITY_ADMIN_PASSWORD=
```

## 접속 방법

| 대상 | 주소 |
|---|---|
| Grafana 대시보드 | `https://<도메인>/grafana/` |

Node-RED, InfluxDB, PostgreSQL은 외부에서 직접 접근할 수 없습니다. 서버 내부에서만 `127.0.0.1` 포트로 접근하세요.

## Nginx 설정

- `nginx.conf`에서 `/grafana/` 경로를 Grafana 컨테이너로 프록시합니다.
- Let's Encrypt 인증서는 호스트의 `/etc/letsencrypt`를 읽기 전용으로 마운트합니다.
- 설정 변경 후에는 `docker compose restart nginx`로 반영하세요.

## Grafana 플러그인

컨테이너 기동 시 다음 플러그인이 자동 설치됩니다.

- influxdb
- grafana-postgresql-datasource
- yesoreyeram-infinity-datasource
- marcusolsson-dynamictext-panel
- cloudspout-button-panel

## Node-RED 참고 사항

- `nodered_data/`를 `/data`로 마운트하며, 로컬에서 편집한 `flows.json`이 컨테이너에 반영됩니다.
- 컨테이너 기동 시 `npm install --prefix /data`로 `package.json`의 패키지를 자동 설치합니다.

## 보안 주의 사항

- `.env`와 DB 데이터 폴더(`*_data/`, `influxdb_config/`)는 `.gitignore`에 추가하세요.
- InfluxDB 관리자 토큰은 반드시 환경변수로 관리하고, 이미 저장소에 노출된 토큰은 폐기 후 재발급하세요.
- 데모 공개 시 Grafana 익명 접속 설정은 기본적으로 비활성화되어 있습니다(`docker-compose.yml` 주석 참고).

## 라이선스

<!-- 라이선스를 정해 주세요. 예: MIT -->
TBD
