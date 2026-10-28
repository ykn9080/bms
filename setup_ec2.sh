#!/bin/bash

# 💡 이 스크립트는 EC2 서버 내부 내부에서 수행되는 역할입니다.
ARCHIVE_NAME="my_iot_backup.tar.gz"

echo "🐳 [EC2] 1. Docker 및 Docker Compose 설치 상태 확인 중..."
if ! command -v docker &> /dev/null; then
  echo "⚠️ Docker가 없습니다. 최초 설치 및 자동 시작 등록을 진행합니다..."
  sudo dnf update -y
  sudo dnf install docker -y
  sudo dnf install docker-compose-plugin -y

  # 인스턴스 재시작 시 Docker가 자동 시작되도록 등록
  sudo systemctl enable docker
  sudo systemctl start docker

  # 현재 계정에 Docker 그룹 권한 부여
  sudo usermod -aG docker $USER

   echo "========== Docker Compose 설치 시작 =========="
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
if [ ! -f /usr/bin/docker-compose ]; then
    sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
fi

# 1. Docker 플러그인 폴더 생성 (이미 있으면 통과)
sudo mkdir -p /usr/libexec/docker/cli-plugins

# 2. 기존 실행 가능한 컴포즈 파일을 플러그인 폴더로 링크 연결
sudo ln -s $(which docker-compose) /usr/libexec/docker/cli-plugins/docker-compose

echo "========== Docker Compose 설치 완료 =========="

# 1. docker 그룹 생성 (보통 이미 생성되어 있습니다)
sudo groupadd docker

# 2. 현재 로그인한 사용자($USER)를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 3. 변경된 그룹 설정을 현재 터미널 세션에 바로 적용
newgrp docker

  echo "✅ Docker 설치 및 활성화 완료!"
else
  echo "✅ Docker가 이미 설치되어 있습니다."
fi



echo "🔄 [EC2] 3. Docker Compose 서비스를 백그라운드로 가동합니다..."

# docker-compose가 있는 디렉토리에서 실행
sudo chown -R 1000:1000 ./influxdb_data ./influxdb_config
sudo chmod -R 755 ./influxdb_data ./influxdb_config
sudo chown -R 472:472 ./grafana_data
sudo chmod -R 755 ./grafana_data


# 권한 안전 조치를 위해 sudo를 포함하여 서비스를 새로고침합니다.
sudo docker compose down
sudo docker compose up -d --remove-orphans

# node-red pallette 재설치
docker exec -u 0 -it node-red npm install --prefix /data

echo "🧹 [EC2] 4. 원격 세팅 스크립트 자가 청소..."
rm -f /home/$USER/$ARCHIVE_NAME
#rm -f /home/$USER/setup_ec2.sh

echo "🏁 [EC2] 모든 컨테이너가 성공적으로 구동되었으며, 서버 재시작 자동화가 완료되었습니다!"
