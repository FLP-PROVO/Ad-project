'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import { Ad } from '@/lib/types';

export default function AdsPage() {
  const [ads, setAds] = useState<Ad[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadAds = async () => {
      try {
        const result = await apiFetch<Ad[]>('/api/v1/ads/available', {}, true);
        setAds(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : '広告一覧の取得に失敗しました');
      }
    };

    void loadAds();
  }, []);

  return (
    <section>
      <h1>視聴可能な広告</h1>
      {error && <p className="error">{error}</p>}
      {ads.length === 0 && !error && <p>現在視聴可能な広告はありません。</p>}
      {ads.map((ad) => (
        <article className="card" key={ad.id}>
          <h2>{ad.title}</h2>
          <p>報酬ポイント: {ad.reward_point}</p>
          <p>残予算: {ad.remaining_budget}</p>
          <Link href={`/ads/${ad.id}`}>この広告を視聴する</Link>
        </article>
      ))}
    </section>
  );
}
