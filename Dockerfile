FROM python:3.11-slim

WORKDIR /app

# 한글 폰트 (NanumGothic) 설치 - 워드클라우드 한글 렌더링용
# curl 추가 - 헬스체크용
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 고가용성을 위한 worker 설정 (메모리 사용량 고려하여 2개로 조정)
CMD ["gunicorn", "app:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "100"]
