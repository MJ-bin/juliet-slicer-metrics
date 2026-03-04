#!/bin/bash
# ──────────────────────────────────────────────────────────
# run_pipeline.sh
#
# 호스트에서 실행하며, 컨테이너에 스크립트를 복사하고
# 의존성 설치 → 슬라이스 생성 → 토큰화를 순차적으로 수행한다.
#
# 사용법:
#   ./run_pipeline.sh <container_id>
#
# 예시:
#   ./run_pipeline.sh 432219f99fcb
# ──────────────────────────────────────────────────────────
set -e

if [ -z "$1" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Usage: $0 <container_id>"
    exit 1
fi

CONTAINER_ID="$1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMOTE_DIR="/root/infer-experiment/bin"

echo "=========================================="
echo " Target container: ${CONTAINER_ID}"
echo "=========================================="

# 1) 스크립트 복사
echo "[1/4] Copying scripts to container..."
docker cp "${SCRIPT_DIR}/generate_slices.py" "${CONTAINER_ID}:${REMOTE_DIR}/generate_slices.py"
docker cp "${SCRIPT_DIR}/tokenize_slices.py" "${CONTAINER_ID}:${REMOTE_DIR}/tokenize_slices.py"

# 2) 의존성 설치
echo "[2/4] Installing dependencies inside container..."
docker exec "${CONTAINER_ID}" bash -c "\
    apt-get update -qq && \
    apt-get install -y -qq python3-pip > /dev/null 2>&1 && \
    pip3 install transformers scienceplots matplotlib"

# 3) 슬라이스 생성
echo "[3/4] Running generate_slices.py..."
docker exec "${CONTAINER_ID}" python3 "${REMOTE_DIR}/generate_slices.py"

# 4) 토큰화 및 그래프 생성
echo "[4/4] Running tokenize_slices.py..."
docker exec "${CONTAINER_ID}" python3 "${REMOTE_DIR}/tokenize_slices.py"

echo ""
echo "=========================================="
echo " Done!"
echo "=========================================="
