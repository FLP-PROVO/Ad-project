# Ad View Rewards Frontend (Next.js)

閲覧者フローの最小構成フロントエンドです。FastAPI バックエンドに `fetch` で直接アクセスします。

## 対応フロー

- `/register`: 新規登録（成功時 JWT 保存）
- `/login`: ログイン（JWT 保存）
- `/ads`: 視聴可能広告一覧の表示 (`GET /api/v1/ads/available`)
- `/ads/[id]`: 視聴ページ（表示時に `POST /start`、完了ボタンで `POST /complete`）
- `/profile`: 残高と台帳の表示

> JWT は `localStorage` (`avr_access_token`) に保存します。

## 前提

- Node.js 18+
- バックエンドがローカルで起動済み（例: `http://localhost:8000`）

## セットアップ

```bash
cd ad-view-rewards/frontend
npm install
```

## 起動（開発モード）

```bash
npm run dev
```

デフォルト: `http://localhost:3000`

## バックエンド URL の変更

環境変数 `NEXT_PUBLIC_API_BASE_URL` を指定してください。

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

## 実行スクリプト

- `npm run dev`: 開発サーバー起動
- `npm run build`: 本番ビルド
- `npm run start`: 本番モード起動
- `npm run lint`: ESLint
- `npm run test:e2e`: Playwright E2E（スケルトン）

## 注意点

- 完了ボタンは、`処理中` または `reward_granted=true` の場合に無効化し、連打による重複送信をクライアント側で抑制しています。
- ただし最終的な重複防止はバックエンド側の整合性ロジックに依存します。

## バックエンドと合わせた最短確認手順

1. バックエンドを起動（`ad-view-rewards/backend`）。
2. フロントエンドを起動（`ad-view-rewards/frontend`）。
3. `/register` でユーザー作成。
4. `/ads` で広告一覧確認。
5. 任意の広告 `/ads/[id]` で視聴開始→完了。
6. `/profile` で残高・台帳更新を確認。
