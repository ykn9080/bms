# BMS 데모 시스템 / BMS Demo System

Docker Compose 기반의 BMS(건물 관리 시스템) 데모입니다. 가상 센서 데이터를 생성하고, AWS IoT MQTT로 발행·구독한 뒤, 시계열 DB와 관계형 DB에 나누어 저장하고, Grafana 대시보드로 시각화합니다.

A BMS (Building Management System) demo built with Docker Compose. It generates virtual sensor data, publishes and subscribes it over AWS IoT MQTT, stores it in a time-series DB and a relational DB, and visualizes it on a Grafana dashboard.

- 🌐 데모 사이트 / Demo site: https://yknam.duckdns.org
- 📄 소개 페이지 (한국어/English) / Introduction page (KO/EN): https://ykn9080.github.io/bms/

## 주요 기능 / Key Features

- **가상 센서 데이터 생성** / **Virtual sensor data generation**: BMS 센서/장비 데이터를 시나리오에 따라 생성 / Generates BMS sensor and equipment data according to scenarios
- **백엔드 프로세스 처리** / **Backend process engine**: Node-RED로 데이터 생성, 판별, 전송 흐름 구성 / Node-RED flows for generation, judgment, and transmission
- **AWS IoT MQTT 발행·구독** / **AWS IoT MQTT publish/subscribe**: 데이터를 클라우드 토픽으로 발행하고 구독하여 저장 / Publishes data to cloud topics and subscribes to store it
- **데이터 이원화 저장** / **Dual storage**
  - InfluxDB: IoT 시계열 데이터 전체 / All IoT time-series data
  - PostgreSQL: 비정상 데이터만 선별 저장 / Abnormal data only
- **대시보드** / **Dashboard**: Grafana로 차트 및 데모 화면 제공 / Charts and demo screens with Grafana
- **외부 공개 최소화** / **Minimal external exposure**: Nginx 리버스 프록시만 외부에 공개 / Only the Nginx reverse proxy is public

## 시스템 구성 / Architecture

```
[사용자 브라우저 / User browser]
       │ HTTPS (443)
       ▼
[Nginx] ── reverse proxy ──▶ [Grafana] ── 쿼리 / query ──▶ [InfluxDB]
                                     └──── 쿼리 / query ──▶ [PostgreSQL]

[BMS 센서/장비 / BMS devices (가상데이터 생성 / virtual data)]
       │
       ▼
[Node-RED] 백앤드프로세스엔진 / backend process engine
       ├─▶ [InfluxDB]    IoT 시계열 전체 / all time-series data
       └─▶ [PostgreSQL]  비정상 데이터만 / abnormal data only
```

| 서비스 / Service | 이미지 / Image | 역할 / Role | 외부 노출 / Exposed |
|---|---|---|---|
| nginx | `nginx:alpine` | 리버스 프록시, HTTPS / Reverse proxy, HTTPS | 80, 443 |
| grafana | `grafana/grafana:11.5.2` | 차트 및 데모 시스템 / Charts and demo | 내부 / Internal |
| node-red | `nodered/node-red:latest` | 백엔드 프로세스 엔진 / Backend process engine | 내부 / Internal |
| influxdb | `influxdb:2.7-alpine` | IoT용 시계열 DB / IoT time-series DB | 내부 / Internal |
| postgres | `postgres:15-alpine` | 비정상 데이터 저장 / Abnormal data storage | 내부 / Internal |

모든 서비스는 `iot-network` 브리지 네트워크에서 동작하며, Nginx를 제외한 서비스는 `127.0.0.1`에만 바인딩됩니다.
All services run on the `iot-network` bridge network. Except for Nginx, every service is bound only to `127.0.0.1`.

## 디렉터리 구조 / Directory Structure

```
.
├── docker-compose.yml
├── nginx.conf
├── .env                # 민감 정보, Git에 올리지 않음 / Secrets, not committed
├── .env.example
├── nodered_data/       # flows.json, package.json
├── grafana_data/
├── influxdb_data/
├── influxdb_config/
└── postgres_data/
```

## 사전 준비 / Prerequisites

- Docker 및 Docker Compose / Docker and Docker Compose
- 도메인 (데모에서는 DuckDNS 사용) / A domain (the demo uses DuckDNS)
- HTTPS 인증서 (Let's Encrypt, `/etc/letsencrypt`) / HTTPS certificate (Let's Encrypt, `/etc/letsencrypt`)
- AWS IoT Core 엔드포인트와 인증서 / AWS IoT Core endpoint and certificates

## 설치 및 실행 / Installation and Usage

1. 저장소 클론 / Clone the repository

   ```bash
   git clone https://github.com/ykn9080/bms.git
   cd bms
   ```

2. 환경변수 파일 준비 / Prepare the environment file

   ```bash
   cp .env.example .env
   # .env를 열어 실제 값을 입력 / Open .env and fill in your values
   ```

3. 컨테이너 실행 / Start the containers

   ```bash
   docker compose up -d
   ```

4. 상태 확인 / Check the status

   ```bash
   docker compose ps
   docker compose logs -f
   ```

## 환경변수 (.env) / Environment Variables

`.env.example`에 다음 항목을 정의하세요. / Define the following in `.env.example`.

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

## 접속 방법 / Access

| 대상 / Target | 주소 / URL |
|---|---|
| Grafana 대시보드 / dashboard | `https://<도메인 / domain>/grafana/` |

Node-RED, InfluxDB, PostgreSQL은 외부에서 직접 접근할 수 없습니다. 서버 내부에서만 `127.0.0.1` 포트로 접근하세요.
Node-RED, InfluxDB, and PostgreSQL cannot be reached directly from outside. Access them only from inside the server via `127.0.0.1` ports.

## Nginx 설정 / Nginx Configuration

- `nginx.conf`에서 `/grafana/` 경로를 Grafana 컨테이너로 프록시합니다. / `nginx.conf` proxies the `/grafana/` path to the Grafana container.
- Let's Encrypt 인증서는 호스트의 `/etc/letsencrypt`를 읽기 전용으로 마운트합니다. / Let's Encrypt certificates are mounted read-only from the host's `/etc/letsencrypt`.
- 설정을 바꾼 뒤에는 `docker compose restart nginx`로 반영하세요. / After changing the config, apply it with `docker compose restart nginx`.

## Grafana 플러그인 / Grafana Plugins

컨테이너 기동 시 다음 플러그인이 자동 설치됩니다. / The following plugins are installed automatically at startup.

- influxdb
- grafana-postgresql-datasource
- yesoreyeram-infinity-datasource
- marcusolsson-dynamictext-panel
- cloudspout-button-panel

## Node-RED 참고 사항 / Node-RED Notes

- `nodered_data/`를 `/data`로 마운트하므로 로컬에서 편집한 `flows.json`이 컨테이너에 반영됩니다. / `nodered_data/` is mounted to `/data`, so edits to `flows.json` apply to the container.
- 기동 시 `npm install --prefix /data`로 `package.json`의 패키지를 자동 설치합니다. / On startup, packages in `package.json` are installed automatically with `npm install --prefix /data`.
- AWS IoT MQTT 연결 정보(엔드포인트, 인증서, 토픽)는 Node-RED 노드 설정에서 입력합니다. / AWS IoT MQTT connection details (endpoint, certificates, topics) are entered in the Node-RED node settings.

## 보안 주의 사항 / Security Notes

- `.env`와 DB 데이터 폴더(`*_data/`, `influxdb_config/`)는 `.gitignore`에 추가하세요. / Add `.env` and the database data folders (`*_data/`, `influxdb_config/`) to `.gitignore`.
- InfluxDB 관리자 토큰은 환경변수로 관리하고, 노출된 토큰은 폐기 후 재발급하세요. / Manage the InfluxDB admin token through environment variables, and revoke and reissue any token that has been exposed.
- 데모 공개 시 Grafana 익명 접속은 기본적으로 비활성화되어 있습니다(`docker-compose.yml` 주석 참고). / Anonymous Grafana access is disabled by default for the public demo (see comments in `docker-compose.yml`).

## 라이선스 / License

<!-- 라이선스를 정해 주세요 / Please choose a license -->
TBD
