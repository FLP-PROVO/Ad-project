# Ad View Rewards (MVP) - Backend Scaffold

広告動画視聴でポイントを付与する Web アプリの MVP 向けに、FastAPI + PostgreSQL の最小構成を Docker で立ち上げるための雛形です。

## 前提

- Docker
- Docker Compose (`docker compose` コマンド)
- `backend/Dockerfile` では将来 `ffprobe` を使うために `ffmpeg` をインストールしておく必要があります（Task10 では未実行）。

## ディレクトリ構成

```text
ad-view-rewards/
  backend/
    Dockerfile
    docker-compose.yml
    app/
      main.py
      core/
        config.py
        security.py
      models/
        __init__.py
      schemas/
      routers/
        auth.py
        ads.py
        viewers.py
      services/
      db/
        base.py
        alembic/
    tests/
```

## 起動手順（ローカル開発）

```bash
cd ad-view-rewards/backend
docker compose up --build -d
```

起動確認:

```bash
docker compose ps
```

## ヘルスチェック

```bash
curl -i http://localhost:8000/api/v1/health
```

期待されるレスポンス:

- HTTP 200
- Body: `{"status":"ok"}`

## マイグレーション実行手順

```bash
cd ad-view-rewards/backend
alembic upgrade head
```

DB変更を取り込む際は上記を実行してください。

## テスト実行

### 1) docker-compose でローカル実行（推奨）

```bash
cd ad-view-rewards/backend
docker compose up -d db
docker compose run --rm backend sh -c "pip install -r requirements.txt && flake8 . && pytest -q"
```

### 2) ローカル Python で実行

```bash
cd ad-view-rewards/backend
pip install -r requirements.txt
flake8 .
python -m pytest -q
```

## 停止・後片付け

```bash
cd ad-view-rewards/backend
docker compose down
```

DB ボリュームも削除する場合:

```bash
docker compose down -v
```


## フロントエンド（Next.js）

最小限の閲覧者フロー UI は `frontend/` にあります。

```bash
cd ad-view-rewards/frontend
npm install
npm run dev
```

詳細は `frontend/README.md` を参照してください。
