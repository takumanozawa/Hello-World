FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libgeos-dev \
    gdal-bin \
    libgdal-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetryのインストール
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# 依存関係ファイルのコピー
COPY pyproject.toml poetry.lock* ./

# 依存関係のインストール
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 8000

# アプリケーション起動
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
