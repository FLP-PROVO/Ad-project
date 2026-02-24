# Ad View Rewards (MVP) - Backend Scaffold

広告動画視聴でポイントを付与する Web アプリの MVP 向けに、FastAPI + PostgreSQL の最小構成を Docker で立ち上げるための雛形です。

## 前提

- Docker
- Docker Compose (`docker compose` コマンド)
- `backend/Dockerfile` で `ffmpeg` をインストールし、`ffprobe` コマンドが利用可能であること

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

`ads` テーブルには動画アップロード後に `file_path` / `duration_seconds` / `file_size_bytes` / `status` が更新されます。
マイグレーション適用前後でこれらの列があるかを確認してください。

`ad_views` は視聴開始/完了・報酬状態・`client_info` (JSONB) を保持します。
日次の重複防止インデックス `ux_ad_view_user_ad_date` を使用するため、既存データに重複がある環境で導入する場合は事前クレンジングが必要です。

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

## 管理者向け動画アップロード API

- エンドポイント: `POST /api/v1/admin/ads/{ad_id}/upload`
- 認証: 管理者トークン必須
- 受け付け: `.mp4` のみ、50MB 以下
- サーバー側で `ffprobe` を使って duration を取得し、`duration_seconds >= 15` を満たした場合のみ `ready` 化

内部では以下コマンド相当で duration を取得します。

```bash
ffprobe -v error -show_entries format=duration -of csv="p=0" /path/to/tmpfile.mp4
```

curl 例:

```bash
curl -X POST "http://localhost:8000/api/v1/admin/ads/<ad_id>/upload" \
  -H "Authorization: Bearer <admin_token>" \
  -F "file=@./sample.mp4;type=video/mp4"
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
