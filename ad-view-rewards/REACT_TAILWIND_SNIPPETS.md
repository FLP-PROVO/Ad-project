# AdViewRewards React + Tailwind コードスニペット（モバイルファースト）

以下は **React Functional Components + Tailwind CSS** を前提にした実装例です。  
3画面（広告一覧 / 広告プレイヤー / マイページ）を、再利用可能コンポーネントで構成しています。

---

## デザイントークン（Tailwind拡張例）

### `tailwind.config.js`
```js
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./pages/**/*.{js,jsx}', './components/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: '#0066FF',
        accent: '#00C48C',
        background: '#F8FAFC',
        card: '#FFFFFF',
        textPrimary: '#111827',
        textSecondary: '#6B7280',
      },
      borderRadius: {
        DEFAULT: '8px',
      },
      fontFamily: {
        sans: ['Noto Sans JP', 'system-ui', 'sans-serif'],
      },
      minHeight: {
        tap: '44px',
      },
      minWidth: {
        tap: '44px',
      },
    },
  },
  plugins: [],
};
```

---

## 再利用コンポーネント

### `components/ui/Button.jsx`
```jsx
export default function Button({
  children,
  variant = 'primary',
  type = 'button',
  disabled = false,
  className = '',
  ...props
}) {
  const base =
    'h-10 min-h-tap min-w-tap rounded px-4 text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2';

  const styles = {
    primary: 'bg-primary text-white hover:bg-blue-700 focus-visible:ring-primary disabled:bg-blue-300',
    secondary: 'bg-white border border-slate-200 text-textPrimary hover:bg-slate-50 focus-visible:ring-primary',
    accent: 'bg-accent text-white hover:bg-emerald-600 focus-visible:ring-accent disabled:bg-emerald-300',
    ghost: 'bg-transparent text-textSecondary hover:bg-slate-100 focus-visible:ring-primary',
  };

  return (
    <button type={type} disabled={disabled} className={`${base} ${styles[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
```

### `components/AdCard.jsx`
```jsx
import Button from './ui/Button';

export default function AdCard({ ad, onStart }) {
  return (
    <article className="rounded bg-card p-3 shadow-sm ring-1 ring-slate-100">
      <img
        src={ad.thumbnailUrl}
        alt={`${ad.brandName} の広告サムネイル`}
        className="mb-3 aspect-video w-full rounded object-cover"
      />

      <div className="space-y-1">
        <h2 className="text-base font-semibold text-textPrimary">{ad.title}</h2>
        <p className="text-sm text-textSecondary">{ad.brandName}</p>
      </div>

      <div className="mt-2 flex items-center justify-between">
        <p className="text-sm text-textSecondary">{ad.durationSec}秒</p>
        <span className="rounded bg-emerald-50 px-2 py-1 text-sm font-semibold text-accent">+{ad.rewardPoint}pt</span>
      </div>

      <Button
        className="mt-3 w-full"
        variant="primary"
        onClick={() => onStart(ad.id)}
        aria-label={`${ad.title} の視聴を開始`}
      >
        視聴を開始
      </Button>
    </article>
  );
}
```

### `components/Player.jsx`
```jsx
import { useMemo } from 'react';
import Button from './ui/Button';

export default function Player({
  adId,
  videoUrl,
  poster,
  elapsedSec,
  requiredSec = 15,
  onPlay,
  onTimeUpdate,
  onComplete,
  isCompleting,
}) {
  const progress = useMemo(() => {
    const ratio = Math.min(100, Math.floor((elapsedSec / requiredSec) * 100));
    return Number.isFinite(ratio) ? ratio : 0;
  }, [elapsedSec, requiredSec]);

  const qualified = elapsedSec >= requiredSec;

  return (
    <section className="space-y-4">
      <div className="overflow-hidden rounded bg-black">
        <video
          className="aspect-video w-full"
          src={videoUrl}
          poster={poster}
          controls
          playsInline
          preload="metadata"
          onPlay={onPlay}
          onTimeUpdate={onTimeUpdate}
          aria-label="広告動画プレイヤー"
        />
      </div>

      <div className="rounded bg-card p-4 shadow-sm ring-1 ring-slate-100" aria-live="polite">
        <p className="mb-2 text-sm text-textPrimary">視聴 {Math.floor(elapsedSec)} / {requiredSec} 秒</p>
        <div
          className="h-2 w-full rounded bg-slate-200"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={requiredSec}
          aria-valuenow={Math.floor(elapsedSec)}
        >
          <div
            className={`h-2 rounded ${qualified ? 'bg-accent' : 'bg-primary'}`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="rounded bg-card p-4 shadow-sm ring-1 ring-slate-100">
        <p className="text-sm text-textSecondary">獲得予定</p>
        <p className="text-2xl font-bold text-accent">+30pt</p>
        <p className="mt-1 text-xs text-textSecondary">15秒以上の視聴で受け取り可能</p>
      </div>

      <Button
        variant="accent"
        className="w-full"
        disabled={!qualified || isCompleting}
        onClick={() => onComplete(adId)}
      >
        {isCompleting ? '処理中...' : '報酬を受け取る'}
      </Button>
    </section>
  );
}
```

### `components/BalanceCard.jsx`
```jsx
export default function BalanceCard({ totalPoint, updatedAt }) {
  return (
    <section className="rounded bg-card p-4 shadow-sm ring-1 ring-slate-100">
      <p className="text-sm text-textSecondary">現在の残高</p>
      <p className="mt-1 text-3xl font-bold text-textPrimary">{totalPoint.toLocaleString()}pt</p>
      <p className="mt-2 text-xs text-textSecondary">最終更新: {updatedAt}</p>
    </section>
  );
}
```

---

## 画面1: 広告一覧

### `pages/ads/index.jsx`
```jsx
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import AdCard from '../../components/AdCard';

export default function AdsPage() {
  const router = useRouter();
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAds = async () => {
      try {
        const res = await fetch('/api/v1/ads');
        const data = await res.json();
        setAds(data.items ?? []);
      } catch (err) {
        console.error('failed to fetch ads', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAds();
  }, []);

  const handleStart = (adId) => {
    router.push(`/ads/${adId}`);
  };

  return (
    <main className="min-h-screen bg-background px-4 py-4 text-textPrimary">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">広告一覧</h1>
        <div className="rounded bg-card px-3 py-2 text-sm shadow-sm ring-1 ring-slate-100">残高 1,240pt</div>
      </header>

      {loading ? (
        <p className="text-sm text-textSecondary" aria-busy="true">読み込み中...</p>
      ) : (
        <section className="space-y-3">
          {ads.map((ad) => (
            <AdCard key={ad.id} ad={ad} onStart={handleStart} />
          ))}
        </section>
      )}
    </main>
  );
}
```

---

## 画面2: 広告プレイヤー

### `pages/ads/[id].jsx`
```jsx
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Player from '../../components/Player';

export default function AdPlayerPage() {
  const router = useRouter();
  const { id: adId } = router.query;

  const [ad, setAd] = useState(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    if (!adId) return;

    const fetchAdDetail = async () => {
      try {
        const res = await fetch(`/api/v1/ads/${adId}`);
        const data = await res.json();
        setAd(data);
      } catch (err) {
        console.error('failed to fetch ad detail', err);
      }
    };

    fetchAdDetail();
  }, [adId]);

  const handlePlay = async () => {
    if (!adId) return;
    try {
      await fetch(`/api/v1/ads/${adId}/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (err) {
      console.error('failed to start ad session', err);
    }
  };

  const handleTimeUpdate = (event) => {
    setElapsedSec(event.currentTarget.currentTime || 0);
  };

  const handleComplete = async (currentAdId) => {
    setIsCompleting(true);
    try {
      await fetch(`/api/v1/ads/${currentAdId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      alert('報酬を受け取りました。');
      router.push('/mypage');
    } catch (err) {
      console.error('failed to complete ad', err);
      alert('完了処理に失敗しました。通信状況をご確認ください。');
    } finally {
      setIsCompleting(false);
    }
  };

  if (!ad) {
    return (
      <main className="min-h-screen bg-background px-4 py-6">
        <p className="text-sm text-textSecondary">読み込み中...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background px-4 py-4 text-textPrimary">
      <header className="mb-4 flex items-center justify-between">
        <button
          className="min-h-tap min-w-tap rounded px-3 text-sm text-textSecondary hover:bg-slate-100"
          onClick={() => router.back()}
          aria-label="一覧へ戻る"
        >
          戻る
        </button>
        <p className="text-sm text-textSecondary">視聴セッション進行中</p>
      </header>

      <Player
        adId={ad.id}
        videoUrl={ad.videoUrl}
        poster={ad.thumbnailUrl}
        elapsedSec={elapsedSec}
        requiredSec={15}
        onPlay={handlePlay}
        onTimeUpdate={handleTimeUpdate}
        onComplete={handleComplete}
        isCompleting={isCompleting}
      />
    </main>
  );
}
```

---

## 画面3: マイページ

### `pages/mypage/index.jsx`
```jsx
import { useEffect, useState } from 'react';
import BalanceCard from '../../components/BalanceCard';

export default function MyPage() {
  const [wallet, setWallet] = useState({ totalPoint: 0, updatedAt: '-' });
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [walletRes, historyRes] = await Promise.all([
          fetch('/api/v1/wallet'),
          fetch('/api/v1/rewards/history?period=30d'),
        ]);

        const walletData = await walletRes.json();
        const historyData = await historyRes.json();

        setWallet({
          totalPoint: walletData.totalPoint ?? 0,
          updatedAt: walletData.updatedAt ?? '-',
        });
        setHistory(historyData.items ?? []);
      } catch (err) {
        console.error('failed to fetch mypage data', err);
      }
    };

    fetchData();
  }, []);

  return (
    <main className="min-h-screen bg-background px-4 py-4 text-textPrimary">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">マイページ</h1>
        <button className="min-h-tap min-w-tap rounded px-3 text-sm text-textSecondary hover:bg-slate-100">
          設定
        </button>
      </header>

      <div className="space-y-4">
        <BalanceCard totalPoint={wallet.totalPoint} updatedAt={wallet.updatedAt} />

        <section className="rounded bg-card p-4 shadow-sm ring-1 ring-slate-100">
          <h2 className="mb-2 text-base font-semibold">履歴</h2>

          {history.length === 0 ? (
            <p className="text-sm text-textSecondary">まだ履歴がありません。</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {history.map((item) => (
                <li key={item.id} className="flex min-h-[56px] items-center justify-between py-3">
                  <div>
                    <p className="text-sm text-textPrimary">{item.type}</p>
                    <p className="text-xs text-textSecondary">{item.createdAt}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-accent">+{item.point}pt</p>
                    <p className="text-xs text-textSecondary">{item.status}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}
```
