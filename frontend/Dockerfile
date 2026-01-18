FROM node:20-alpine

WORKDIR /app

# pnpmのインストール
RUN npm install -g pnpm

# 依存関係ファイルのコピー
COPY package.json pnpm-lock.yaml* ./

# 依存関係のインストール
RUN pnpm install --frozen-lockfile

# アプリケーションコードのコピー
COPY . .

# ポート公開
EXPOSE 3000

# 開発サーバー起動
CMD ["pnpm", "dev"]
