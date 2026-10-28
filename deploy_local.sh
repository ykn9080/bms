#!/bin/bash

# 에러 발생 시 즉시 중단되도록 설정
set -e

# ================= 사용자 설정 부분 =================
EC2_IP="3.39.25.21"
EC2_USER="ec2-user"
PEM_KEY="/home/yknam/docker_project/aws_certs/ec2.pem"
ARCHIVE_NAME="iot_project.tar.gz"
# ====================================================

echo "🚀 [1/6] 이전 압축 파일이 있다면 청소합니다..."
rm -f $ARCHIVE_NAME

echo "🔓 [1-1/6] 도커 데이터 폴더의 권한을 내 유저 소유로 안전하게 조정 중..."
sudo chown -R $USER:$USER ./grafana_data || true
sudo chmod -R 755 ./grafana_data || true

echo "🔄 [2/6] EC2용 설정 파일명을 표준 이름(.env, docker-compose.yml)으로 임시 변경 중..."
[ -f .env ] && mv -f .env .env_local_bak || true
[ -f docker-compose.yml ] && mv -f docker-compose.yml docker-compose_local_bak || true

if [ ! -f ".env-ec2" ] || [ ! -f "docker-compose-ec2.yml" ]; then
    echo "❌ 에러: .env-ec2 또는 docker-compose-ec2.yml 파일이 현재 폴더에 없습니다."
    [ -f .env_local_bak ] && mv -f .env_local_bak .env || true
    [ -f docker-compose_local_bak ] && mv -f docker-compose_local_bak docker-compose.yml || true
    exit 1
fi

cp .env-ec2 .env
cp docker-compose-ec2.yml docker-compose.yml

echo "📦 [3/6] 무거운 폴더 및 불필요한 파일을 제외하고 압축 중..."
set +e
tar --exclude="$ARCHIVE_NAME" \
    --exclude='nodered_data/node_modules' \
    --exclude='grafana_data/plugins' \
    --exclude='deploy_local.sh' \
    --exclude='deploy.sh' \
    --exclude='docker-compose.yml.save' \
    --exclude='docker-compose.yml.bak' \
    --exclude='extract_nodered.sh' \
    --exclude='nodered_backup' \
    --exclude='pgadmin_data' \
    --exclude='.git' \
    -czvf $ARCHIVE_NAME .
set -e

echo "♻️ [4/6] 압축이 완료되어 로컬 파일명을 원래대로 안전하게 복구 중..."
#rm -f .env docker-compose.yml
[ -f .env_local_bak ] && mv -f .env_local_bak .env || true
[ -f docker-compose_local_bak ] && mv -f docker-compose_local_bak docker-compose.yml || true

echo "🚚 [5/6] EC2 서버로 압축 파일 전송 중..."
if [ ! -f "$PEM_KEY" ]; then
    echo "❌ 에러: 지정한 경로에 키 파일이 없습니다: $PEM_KEY"
    exit 1
fi
chmod 400 "$PEM_KEY"

scp -i "$PEM_KEY" $ARCHIVE_NAME $EC2_USER@$EC2_IP:/home/$EC2_USER/

echo "🏗️ [6/6] EC2 내부에서 압축을 먼저 푼 뒤 스크립트 실행..."
# 💡 [핵심 수정]: 하드코딩되어 있던 구버전 경로를 제거하고, 상단에서 정의한 "$PEM_KEY" 변수를 사용하도록 수정했습니다.
ssh -i "$PEM_KEY" $EC2_USER@$EC2_IP "tar -xzvf $ARCHIVE_NAME && bash /home/$EC2_USER/setup_ec2.sh"

echo "🎉 모든 배포 작업이 완벽하게 끝났습니다."
