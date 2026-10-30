# BMS 데모 시스템

**한국어** | [English](README.en.md)

AWS EC2 위에서 Docker Compose로 실행하는 BMS(건물 관리 시스템) 데모입니다. 가상 센서 데이터를 생성하고, AWS IoT Core로 MQTT 발행·구독한 뒤, 시계열 DB와 관계형 DB에 나누어 저장하고, Grafana 대시보드로 시각화합니다.

- 🌐 데모 사이트: https://yknam.duckdns.org
- 📄 소개 페이지: https://ykn9080.github.io/bms/

## 주요 기능

- **가상 센서 데이터 생성**: 시나리오에 따라 BMS 센서/장비 데이터를 생성
- **이상 감지 및 자동 제어 시뮬레이션**: 온도, CO2, 습도 이상 시 AHU·히터·쿨러를 시뮬레이션으로 가동해 정상 복귀
- **백엔드 프로세스 처리**: Node-RED로 데이터 생성, 판별, 전송 흐름 구성
- **AWS IoT Core MQTT 발행·구독**: 데이터를 클라우드 토픽으로 발행하고 구독하여 InfluxDB에 저장
- **데이터 이원화 저장**
  - InfluxDB: 구독한 IoT 시계열 데이터 전체
  - PostgreSQL: 이상 데이터만 Node-RED에서 직접 저장
- **대시보드**: Grafana로 차트 및 데모 화면 제공
- **외부 공개 최소화**: Nginx 리버스 프록시만 외부에 공개

## 시스템 구성

모든 서비스는 AWS EC2 인스턴스에서 Docker로 실행됩니다. AWS IoT Core는 관리형 서비스로 EC2 밖에서 동작합니다.

```
[사용자 브라우저]
       │ HTTPS (443)
       ▼
[Nginx] ── proxy ──▶ [Grafana] ── 조회 ──▶ [InfluxDB]
                                  └─ 조회 ─▶ [PostgreSQL]

[BMS 센서/장비 (가상 데이터)]
       │
       ▼
[Node-RED] 백앤드프로세스엔진
       ├─ publish ─▶ [AWS IoT Core (MQTT)] ─ subscribe ─▶ [Node-RED] ─▶ [InfluxDB]   전체 저장
       └──────────────────────────────────────────────────────────────▶ [PostgreSQL] 이상 데이터만
```

| 서비스 | 이미지 | 역할 | 외부 노출 |
|---|---|---|---|
| nginx | `nginx:alpine` | 리버스 프록시, HTTPS | 80, 443 |
| grafana | `grafana/grafana:11.5.2` | 차트 및 데모 시스템 | 내부 |
| node-red | `nodered/node-red:latest` | 백엔드 프로세스 엔진 | 내부 |
| influxdb | `influxdb:2.7-alpine` | IoT용 시계열 DB | 내부 |
| postgres | `postgres:15-alpine` | 이상 데이터 저장 | 내부 |

모든 서비스는 `iot-network` 브리지 네트워크에서 동작하며, Nginx를 제외한 서비스는 `127.0.0.1`에만 바인딩됩니다.

## 데모 시나리오

| 시나리오 | 내용 | 현황 |
|---|---|---|
| A. 이상 감지 자동 제어 | 온도·CO2·습도 이상 감지 시 AHU·히터·쿨러 자동 가동으로 정상 복귀 | 시뮬레이션 구현 완료 |
| B. 예지 보전 | 진동·전류 기반 FMEA 예지 보전 | 계획 |
| C. 재실 기반 조명 제어 | 재실 감지 기반 디밍 제어 | 재실·조도 연동 시뮬레이션 구현 |

## 디렉터리 구조

```
.
├── docker-compose.yml
├── nginx.conf
├── .env                # 민감 정보, Git에 올리지 않음
├── .env_example
├── nodered_data/       # flows.json, package.json
└── grafana.json
```

## 사전 준비

- AWS EC2 인스턴스 (Ubuntu)
- Docker 및 Docker Compose
- 도메인 (데모에서는 DuckDNS 사용)
- HTTPS 인증서 (Let's Encrypt, `/etc/letsencrypt`)
- AWS IoT Core 엔드포인트와 인증서

## 설치 및 실행

1. 저장소 클론

   ```bash
   git clone https://github.com/ykn9080/bms.git
   cd bms
   ```

2. 환경변수 파일 준비

   ```bash
   cp .env_example .env
   # .env를 열어 실제 값을 입력
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

`.env_example`에 다음 항목을 정의하세요.

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
- 설정을 바꾼 뒤에는 `docker compose restart nginx`로 반영하세요.

## Grafana 플러그인

컨테이너 기동 시 다음 플러그인이 자동 설치됩니다.

- influxdb
- grafana-postgresql-datasource
- yesoreyeram-infinity-datasource
- marcusolsson-dynamictext-panel
- cloudspout-button-panel

## Node-RED 참고 사항

- `nodered_data/`를 `/data`로 마운트하므로 로컬에서 편집한 `flows.json`이 컨테이너에 반영됩니다.
- 기동 시 `npm install --prefix /data`로 `package.json`의 패키지를 자동 설치합니다.
- AWS IoT Core MQTT 연결 정보(엔드포인트, 인증서, 토픽)는 Node-RED 노드 설정에서 입력합니다.

## 향후 방향

- 현재 목표: BMS 인프라 구축 → 데이터 기반 모니터링 → 통합관리시스템
- 향후: OPEX 최적화, CAPEX 보호, ESG 대응
- 이상 데이터 패턴 분석을 통한 예지 보전 전략 수립
- BACnet/IP 기반 실데이터 연동
