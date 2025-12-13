FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 依存インストールのキャッシュ効率を高めるため、先に requirements をコピーする
COPY requirements.txt /app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# アプリケーションコードを配置
COPY . /app

EXPOSE 8080

CMD ["python", "server.py"]
