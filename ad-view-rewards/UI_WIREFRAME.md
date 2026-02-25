# AdViewRewards モバイルファーストUI設計（ワイヤーフレーム相当）

## 共通デザイン原則（全画面適用）
- **トーン**: 清潔感・信頼感を最優先。情報の階層を明確化し、金融アプリのような落ち着いたUI。
- **デザイン・トークン**
  - Primary: `#0066FF`
  - Accent: `#00C48C`
  - Background: `#F8FAFC`
  - Card: `#FFFFFF`
  - Text primary: `#111827`
  - Text secondary: `#6B7280`
  - Border radius: `8px`
  - Base font: `Noto Sans JP` 相当, base-size: `16px`
  - Button height: `40px`（ただしタップ領域は `min 44x44px`）
- **レイアウト基本**
  - モバイル基準: 幅 `390px`、左右余白 `16px`、セクション間余白 `16〜24px`
  - デスクトップ: 最大幅 `1200px`、中央寄せ、必要に応じて2カラム化
- **ナビゲーション**
  - モバイル: 下部タブ（広告一覧 / マイページ）＋ヘッダー最小
  - デスクトップ: 左サイドナビまたは上部ナビ

---

## 1. ランディング（簡潔にCTA）

### 画面名
ランディング

### 目的（1文）
初回ユーザーに「15秒以上視聴でポイント獲得」という価値を短時間で理解させ、サインアップへ誘導する。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- ヘッダー: ロゴ + ログインリンク
- メイン: 1カラム（ヒーロー、信頼訴求、CTA）
- フッター: 利用規約 / プライバシー / 会社情報

### キーコンポーネント（props相当）
- `Header`
  - `logoText`, `loginHref`, `isSticky`
- `HeroSection`
  - `headline`, `subcopy`, `primaryCtaLabel`, `primaryCtaHref`, `secondaryCtaLabel`, `secondaryCtaHref`
- `FeatureList`
  - `items[{title, description, icon}]`
- `TrustBadgeRow`
  - `badges[{label}]`
- `FooterLinks`
  - `links[{label, href}]`

### 主要要素の簡易HTML（構造のみ、class名を付与）
```html
<div class="page landing-page">
  <header class="header">
    <a class="logo" href="/">AdViewRewards</a>
    <a class="link-login" href="/auth/login">ログイン</a>
  </header>

  <main class="main">
    <section class="hero-card">
      <h1 class="hero-title">広告視聴で、毎日コツコツポイント獲得</h1>
      <p class="hero-copy">動画を15秒以上視聴すると報酬を受け取れます。</p>
      <div class="hero-actions">
        <a class="btn btn-primary" href="/auth/signup">無料ではじめる</a>
        <a class="btn btn-secondary" href="/ads">広告を見る</a>
      </div>
    </section>

    <section class="feature-list">
      <article class="feature-item"></article>
      <article class="feature-item"></article>
      <article class="feature-item"></article>
    </section>
  </main>

  <footer class="footer-links"></footer>
</div>
```

### スタイルの指針
- 見出し: `24px/700`、本文: `16px/400`、補足: `14px/400`
- ボタン: 高さ `40px`、角丸 `8px`、横padding `16px`、実タップ領域 `44px` 以上
- ヒーローカード: 背景 `#FFFFFF`、罫線ごく薄く、余白 `20px`

### インタラクション（再生開始時に呼ぶAPIなど）
- 「無料ではじめる」クリック: `GET /auth/signup` へ遷移（計測 `POST /events/cta-click`）
- 「広告を見る」クリック: 未ログイン時はログイン導線へリダイレクト

### アクセシビリティ注意点
- メインCTAは `aria-label="無料ではじめる（新規登録）"`
- コントラスト比: Primaryボタンの文字は4.5:1以上
- キーボードフォーカスリング（`outline`）を明示

### Acceptance criteria
- 3秒以内にサービス価値（15秒視聴で報酬）が認識できる
- ファーストビュー内に主要CTAが1つ以上表示される
- 390px幅で横スクロールが発生しない
- 主要操作要素が44x44px以上のタップ領域を持つ

---

## 2. サインアップ / ログイン

### 画面名
認証（サインアップ / ログイン）

### 目的（1文）
最小入力で安全にアカウント作成・ログインを完了させる。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- ヘッダー: 戻るボタン + タイトル
- メイン: 1カラム（タブ切替 + フォーム）
- フッター: 法的同意文

### キーコンポーネント（props相当）
- `AuthTabs`
  - `activeTab`, `tabs[{key, label}]`, `onChange`
- `AuthForm`
  - `mode`, `email`, `password`, `confirmPassword`, `onSubmit`, `isLoading`, `errorMessage`
- `TextField`
  - `label`, `type`, `name`, `value`, `placeholder`, `required`, `autocomplete`, `error`
- `SubmitButton`
  - `label`, `disabled`, `loading`

### 主要要素の簡易HTML
```html
<div class="page auth-page">
  <header class="header">
    <button class="icon-btn" aria-label="戻る"></button>
    <h1 class="title">アカウント</h1>
  </header>

  <main class="main">
    <div class="auth-tabs" role="tablist"></div>

    <form class="auth-form" novalidate>
      <label class="field">
        <span class="label">メールアドレス</span>
        <input class="input" type="email" name="email" autocomplete="email" />
      </label>
      <label class="field">
        <span class="label">パスワード</span>
        <input class="input" type="password" name="password" autocomplete="current-password" />
      </label>
      <button class="btn btn-primary" type="submit">続行</button>
    </form>
  </main>

  <footer class="legal-note"></footer>
</div>
```

### スタイルの指針
- 入力高さ: `44px`、角丸 `8px`、境界線は薄いグレー
- エラー文: `12-13px`, 色は視認性重視（赤系）
- タブ: アクティブ時のみPrimary下線

### インタラクション
- サインアップ送信: `POST /api/auth/signup`
- ログイン送信: `POST /api/auth/login`
- 成功時: `GET /api/users/me` 後に広告一覧へ遷移
- 失敗時: フィールド下にバリデーションエラー表示

### アクセシビリティ注意点
- `label for` と `input id` の関連付け
- `aria-invalid="true"` と `aria-describedby` でエラー紐付け
- パスワード表示切替ボタンに `aria-pressed` を付与

### Acceptance criteria
- サインアップ/ログインの切替が1タップで可能
- 必須項目未入力時に送信不可または明確なエラー表示
- 成功時に確実にセッションが作成される
- フォーム要素がスクリーンリーダーで正しく読み上げられる

---

## 3. 広告一覧（カードリスト）

### 画面名
広告一覧

### 目的（1文）
視聴可能な広告と獲得予定ポイントを一覧で提示し、再生開始までの操作負荷を最小化する。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- ヘッダー: 残高サマリー + 通知アイコン
- メイン: 1カラムのカードリスト
- フッター: 下部タブナビ

### キーコンポーネント（props相当）
- `BalanceChip`
  - `points`, `updatedAt`
- `AdCard`
  - `adId`, `title`, `brandName`, `durationSec`, `rewardPoint`, `thumbnailUrl`, `availability`, `onStart`
- `FilterBar`
  - `sort`, `category`, `onChange`
- `BottomTabNav`
  - `activeKey`, `items[{key, label, icon, href}]`

### 主要要素の簡易HTML
```html
<div class="page ads-page">
  <header class="header">
    <div class="balance-chip">残高 1,240pt</div>
    <button class="icon-btn" aria-label="通知"></button>
  </header>

  <main class="main">
    <section class="filter-bar"></section>

    <section class="ad-list">
      <article class="ad-card">
        <img class="ad-thumb" alt="広告サムネイル" />
        <div class="ad-content">
          <h2 class="ad-title">広告タイトル</h2>
          <p class="ad-meta">15秒・+30pt</p>
          <button class="btn btn-primary">視聴を開始</button>
        </div>
      </article>
    </section>
  </main>

  <nav class="bottom-tab"></nav>
</div>
```

### スタイルの指針
- カード内余白 `12〜16px`、カード間 `12px`
- サムネイル比率 `16:9`、角丸 `8px`
- ポイント表示はAccent色を小バッジで強調

### インタラクション
- 一覧取得: `GET /api/ads?status=available`
- 「視聴を開始」: `POST /api/ad-sessions` でセッション開始しプレイヤーへ
- スクロール下端で追加取得（ページング）: `GET /api/ads?cursor=...`

### アクセシビリティ注意点
- カード全体をボタン化する場合は二重フォーカス回避
- サムネイル画像に内容が伝わる `alt` を設定
- ローディング中は `aria-busy="true"`

### Acceptance criteria
- 1画面内で最低2件以上の広告カードを表示可能
- 各カードに「秒数」「報酬pt」「開始ボタン」が存在
- API遅延時にスケルトンまたはローディング表示が出る
- 利用不可広告は無効状態表示になる

---

## 4. 広告再生プレイヤー（最重要）

### 画面名
広告再生プレイヤー

### 目的（1文）
広告を15秒以上の有効視聴として正確に計測し、ユーザーに安心感のある進捗表示と報酬付与結果を提供する。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- ヘッダー: 戻る（必要時） + セッション状態
- メイン: 1カラム（動画プレイヤー、進捗、報酬情報、注意文）
- フッター: 固定アクション（視聴完了後のみ有効）

### キーコンポーネント（props相当）
- `VideoPlayer`
  - `src`, `poster`, `autoplay`, `muted`, `controls`, `onPlay`, `onTimeUpdate`, `onEnded`, `onError`
- `WatchProgress`
  - `elapsedSec`, `requiredSec`, `progressPercent`, `isQualified`
- `RewardStatusCard`
  - `rewardPoint`, `status(locked|pending|granted)`, `sessionId`
- `CompletionButton`
  - `label`, `disabled`, `onClick`
- `SafetyNotice`
  - `text`, `variant(info|warning)`

### 主要要素の簡易HTML
```html
<div class="page player-page">
  <header class="header">
    <button class="icon-btn" aria-label="一覧へ戻る"></button>
    <p class="session-state">視聴セッション進行中</p>
  </header>

  <main class="main">
    <section class="video-wrap">
      <video
        class="video-player"
        playsinline
        preload="metadata"
        aria-label="広告動画プレイヤー"
      ></video>
    </section>

    <section class="progress-card" aria-live="polite">
      <p class="progress-text">視聴 12 / 15 秒</p>
      <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="15" aria-valuenow="12">
        <div class="progress-fill"></div>
      </div>
    </section>

    <section class="reward-card">
      <p class="reward-label">獲得予定</p>
      <p class="reward-value">+30pt</p>
      <p class="reward-state">条件達成で即時付与</p>
    </section>

    <p class="notice">※ 途中離脱した場合は報酬対象外となります。</p>
  </main>

  <footer class="sticky-footer">
    <button class="btn btn-accent" disabled>報酬を受け取る</button>
  </footer>
</div>
```

### スタイルの指針
- 動画領域: 横幅100%、`16:9`、背景ブラック
- 進捗バー高さ: `8px`、達成時にAccentへ色変化
- 「報酬を受け取る」ボタンは固定下部、条件達成までdisabled

### インタラクション
- プレイヤー初期化: `POST /api/ad-sessions`（sessionId発行）
- 再生開始: `POST /api/ad-sessions/{id}/start`
- 1秒ごと進捗送信（または節目）: `POST /api/ad-sessions/{id}/heartbeat`
- 15秒到達時: `POST /api/ad-sessions/{id}/qualify`
- 完了ボタン押下: `POST /api/rewards/claim` → 成功でモーダル表示

### アクセシビリティ注意点
- 進捗値は `aria-live="polite"` で通知し、過剰更新を避ける
- 動画コントロールのキーボード操作（Space/Enter）を担保
- 通信エラー時は音声読み上げ可能なアラート領域を表示

### Acceptance criteria
- 15秒未満で離脱した場合、報酬付与されない
- 15秒到達時にUI状態が「受け取り可能」に変化
- APIエラー時に再試行導線が出る
- 390px幅でプレイヤー・進捗・CTAが1画面内で認識できる

---

## 5. マイページ（残高・履歴）

### 画面名
マイページ

### 目的（1文）
ユーザーが現在残高と報酬履歴を透明性高く確認できるようにする。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- ヘッダー: ユーザー名 / 設定
- メイン: 1カラム（残高カード、履歴リスト）
- フッター: 下部タブナビ

### キーコンポーネント（props相当）
- `BalanceCard`
  - `totalPoint`, `convertibleAmount`, `lastUpdated`
- `HistoryList`
  - `items[{id, type, point, createdAt, status}]`, `onItemClick`
- `HistoryFilter`
  - `period`, `type`, `onChange`
- `SettingsEntry`
  - `label`, `href`, `icon`

### 主要要素の簡易HTML
```html
<div class="page mypage">
  <header class="header">
    <h1 class="title">マイページ</h1>
    <button class="icon-btn" aria-label="設定"></button>
  </header>

  <main class="main">
    <section class="balance-card">
      <p class="label">現在の残高</p>
      <p class="value">1,240pt</p>
    </section>

    <section class="history-section">
      <h2 class="section-title">履歴</h2>
      <ul class="history-list">
        <li class="history-item">
          <span class="history-type">広告視聴</span>
          <span class="history-point">+30pt</span>
        </li>
      </ul>
    </section>
  </main>

  <nav class="bottom-tab"></nav>
</div>
```

### スタイルの指針
- 残高数値は `28px/700` で強調
- 履歴行の高さ `56px` 以上でタップしやすく
- セクションタイトルと本文の階層差を明確に

### インタラクション
- 残高取得: `GET /api/wallet`
- 履歴取得: `GET /api/rewards/history?period=30d`
- フィルタ変更時に再取得

### アクセシビリティ注意点
- 履歴リストは `ul/li` の意味構造を維持
- 日付・数値の読み上げ順を論理的に
- ステータスは色だけでなくテキストでも表示

### Acceptance criteria
- 残高が常に画面上部で確認できる
- 履歴に「日時・種別・ポイント・状態」が表示される
- データ0件時に空状態メッセージが表示される
- 下部タブから広告一覧へ戻れる

---

## 6. 管理ダッシュボード（簡易）

### 画面名
管理ダッシュボード

### 目的（1文）
広告配信と報酬付与の主要指標を簡潔に監視し、異常時の初動を早める。

### レイアウト（ヘッダー/メイン/フッター、カラム数）
- モバイル: 1カラム（KPIカード → テーブル）
- デスクトップ: 2カラム（左KPI、右アラート/テーブル）
- ヘッダー: 日付範囲選択 + 管理者メニュー

### キーコンポーネント（props相当）
- `KpiCard`
  - `label`, `value`, `delta`, `trend(up|down|flat)`
- `DateRangePicker`
  - `startDate`, `endDate`, `onApply`
- `SimpleTable`
  - `columns`, `rows`, `emptyMessage`, `sortable`
- `AlertPanel`
  - `items[{id, level, message, createdAt}]`

### 主要要素の簡易HTML
```html
<div class="page admin-dashboard">
  <header class="header">
    <h1 class="title">管理ダッシュボード</h1>
    <button class="btn btn-secondary">期間変更</button>
  </header>

  <main class="main">
    <section class="kpi-grid">
      <article class="kpi-card"></article>
      <article class="kpi-card"></article>
      <article class="kpi-card"></article>
    </section>

    <section class="alert-panel"></section>

    <section class="table-wrap">
      <table class="data-table">
        <thead></thead>
        <tbody></tbody>
      </table>
    </section>
  </main>
</div>
```

### スタイルの指針
- KPIカード最小高さ `96px`、余白 `16px`
- テーブル文字サイズ `14px`、行高 `44px`
- 警告色は控えめな赤系背景 + 濃色文字

### インタラクション
- KPI取得: `GET /api/admin/metrics?from=...&to=...`
- 異常アラート取得: `GET /api/admin/alerts`
- テーブル並び替え: フロントorAPI（`sortBy`, `order`）

### アクセシビリティ注意点
- テーブルヘッダに `scope="col"`
- 数値の単位（件、pt、%）を明示
- アラート領域は `role="status"` または `role="alert"` を適切に使い分け

### Acceptance criteria
- KPI（再生数、完了率、付与pt等）が即時確認できる
- 期間変更で指標が再計算される
- 異常アラートが時系列で表示される
- モバイルでも表が横スクロールで破綻せず閲覧可能

---

## 補足: レスポンシブ方針
- `<= 767px`: 1カラム固定、下部タブ優先
- `>= 768px`: 余白増加、カード横並び許可
- `>= 1024px`: 管理画面は2カラム化、ユーザー画面は中央寄せで可読性重視

