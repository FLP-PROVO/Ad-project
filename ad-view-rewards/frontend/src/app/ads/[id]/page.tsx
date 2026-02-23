'use client';

import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { Ad, AdView } from '@/lib/types';

export default function AdWatchPage() {
  const params = useParams<{ id: string }>();
  const adId = useMemo(() => params?.id ?? '', [params]);
  const [ad, setAd] = useState<Ad | null>(null);
  const [adView, setAdView] = useState<AdView | null>(null);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    const loadAd = async () => {
      if (!adId) return;

      try {
        const availableAds = await apiFetch<Ad[]>('/api/v1/ads/available', {}, true);
        const currentAd = availableAds.find((item) => item.id === adId) ?? null;
        if (!currentAd) {
          setError('対象の広告が見つかりません。');
          return;
        }

        setAd(currentAd);
        const startRes = await apiFetch<AdView>(`/api/v1/ads/${adId}/start`, { method: 'POST' }, true);
        setAdView(startRes);
        setMessage('視聴開始を記録しました。再生後に完了ボタンを押してください。');
      } catch (e) {
        setError(e instanceof Error ? e.message : '広告情報の取得または開始に失敗しました');
      }
    };

    void loadAd();
  }, [adId]);

  async function onComplete() {
    if (!adId || completing || adView?.reward_granted) {
      return;
    }

    setCompleting(true);
    setError('');
    setMessage('');
    try {
      const completed = await apiFetch<AdView>(`/api/v1/ads/${adId}/complete`, { method: 'POST' }, true);
      setAdView(completed);
      setMessage('完了処理が成功しました。プロフィールで残高を確認してください。');
    } catch (e) {
      setError(e instanceof Error ? e.message : '完了処理に失敗しました');
    } finally {
      setCompleting(false);
    }
  }

  return (
    <section>
      <h1>広告視聴ページ</h1>
      {ad && (
        <article className="card">
          <h2>{ad.title}</h2>
          <video controls width={640} src={ad.video_url} style={{ maxWidth: '100%' }} />
          <p>報酬ポイント: {ad.reward_point}</p>
          <button type="button" onClick={onComplete} disabled={completing || adView?.reward_granted}>
            {adView?.reward_granted ? '報酬付与済み' : completing ? '処理中...' : '完了'}
          </button>
        </article>
      )}
      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
