FROM python:3.11-slim

WORKDIR /app

# 한글 폰트 (NanumGothic) 설치 - 워드클라우드 한글 렌더링용
# curl 추가 - 헬스체크용
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 보안을 위한 non-root 사용자 생성
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 파일 권한 설정
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 고가용성을 위한 worker 설정
# Gunicorn을 사용한 프로덕션 환경 (더 안정적)
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "100"]

# 또는 uvicorn만 사용하는 경우 (개발/테스트 환경)
# CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
