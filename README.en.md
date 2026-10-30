# BMS Demo System

[한국어](README.md) | **English**

A BMS (Building Management System) demo running on AWS EC2 with Docker Compose. It generates virtual sensor data, publishes and subscribes it through AWS IoT Core over MQTT, stores it in a time-series DB and a relational DB, and visualizes it on a Grafana dashboard.

- 🌐 Demo site: https://yknam.duckdns.org
- 📄 Introduction page: https://ykn9080.github.io/bms/

## Key Features

- **Virtual sensor data generation**: Generates BMS sensor and equipment data according to scenarios
- **Anomaly detection and automatic control simulation**: When temperature, CO2, or humidity becomes abnormal, AHU, heater, and cooler are run in simulation to restore normal conditions
- **Backend process engine**: Node-RED flows for generation, judgment, and transmission
- **AWS IoT Core MQTT publish/subscribe**: Publishes data to cloud topics, subscribes, and stores it in InfluxDB
- **Dual storage**
  - InfluxDB: All IoT time-series data received via subscription
  - PostgreSQL: Abnormal data only, written directly from Node-RED
- **Dashboard**: Charts and demo screens with Grafana
- **Minimal external exposure**: Only the Nginx reverse proxy is public

## Architecture

All services run as Docker containers on an AWS EC2 instance. AWS IoT Core is a managed service that runs outside EC2.

```
[User browser]
       │ HTTPS (443)
       ▼
[Nginx] ── proxy ──▶ [Grafana] ── query ──▶ [InfluxDB]
                                  └─ query ─▶ [PostgreSQL]

[BMS sensors/devices (virtual data)]
       │
       ▼
[Node-RED] backend process engine
       ├─ publish ─▶ [AWS IoT Core (MQTT)] ─ subscribe ─▶ [Node-RED] ─▶ [InfluxDB]   save all
       └──────────────────────────────────────────────────────────────▶ [PostgreSQL] abnormal only
```

| Service | Image | Role | Exposed |
|---|---|---|---|
| nginx | `nginx:alpine` | Reverse proxy, HTTPS | 80, 443 |
| grafana | `grafana/grafana:11.5.2` | Charts and demo system | Internal |
| node-red | `nodered/node-red:latest` | Backend process engine | Internal |
| influxdb | `influxdb:2.7-alpine` | IoT time-series DB | Internal |
| postgres | `postgres:15-alpine` | Abnormal data storage | Internal |

All services run on the `iot-network` bridge network. Except for Nginx, every service is bound only to `127.0.0.1`.

## Demo Scenarios

| Scenario | Description | Status |
|---|---|---|
| A. Anomaly detection and auto control | Auto-runs AHU, heater, and cooler on temperature, CO2, or humidity anomalies to restore normal | Simulation implemented |
| B. Predictive maintenance | Vibration- and current-based FMEA predictive maintenance | Planned |
| C. Occupancy-based lighting control | Dimming control based on occupancy detection | Occupancy and illuminance simulation implemented |

## Directory Structure

```
.
├── docker-compose.yml
├── nginx.conf
├── .env                # Secrets, not committed
├── .env_example
├── nodered_data/       # flows.json, package.json
└── grafana.json
```

## Prerequisites

- AWS EC2 instance (Ubuntu)
- Docker and Docker Compose
- A domain (the demo uses DuckDNS)
- HTTPS certificate (Let's Encrypt, `/etc/letsencrypt`)
- AWS IoT Core endpoint and certificates

## Installation and Usage

1. Clone the repository

   ```bash
   git clone https://github.com/ykn9080/bms.git
   cd bms
   ```

2. Prepare the environment file

   ```bash
   cp .env_example .env
   # Open .env and fill in your values
   ```

3. Start the containers

   ```bash
   docker compose up -d
   ```

4. Check the status

   ```bash
   docker compose ps
   docker compose logs -f
   ```

## Environment Variables (.env)

Define the following in `.env_example`.

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

## Access

| Target | URL |
|---|---|
| Grafana dashboard | `https://<domain>/grafana/` |

Node-RED, InfluxDB, and PostgreSQL cannot be reached directly from outside. Access them only from inside the server via `127.0.0.1` ports.

## Nginx Configuration

- `nginx.conf` proxies the `/grafana/` path to the Grafana container.
- Let's Encrypt certificates are mounted read-only from the host's `/etc/letsencrypt`.
- After changing the config, apply it with `docker compose restart nginx`.

## Grafana Plugins

The following plugins are installed automatically at startup.

- influxdb
- grafana-postgresql-datasource
- yesoreyeram-infinity-datasource
- marcusolsson-dynamictext-panel
- cloudspout-button-panel

## Node-RED Notes

- `nodered_data/` is mounted to `/data`, so edits to `flows.json` apply to the container.
- On startup, packages in `package.json` are installed automatically with `npm install --prefix /data`.
- AWS IoT Core MQTT connection details (endpoint, certificates, topics) are entered in the Node-RED node settings.

## Roadmap

- Current goals: BMS infrastructure setup → data-driven monitoring → integrated management system
- Next: OPEX optimization, CAPEX protection, ESG response
- Predictive maintenance strategy based on abnormal data pattern analysis
- Real-data integration over BACnet/IP
