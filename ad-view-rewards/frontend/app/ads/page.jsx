'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import AdCard from '../../components/AdCard';

const MOCK_ADS = [
  {
    id: 'ad-001',
    title: '新NISAの基本を30秒で解説',
    brandName: 'Finance Plus',
    durationSec: 15,
    rewardPoint: 30,
    thumbnailUrl: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80',
  },
  {
    id: 'ad-002',
    title: '家計管理アプリの使い方',
    brandName: 'Wallet Note',
    durationSec: 20,
    rewardPoint: 45,
    thumbnailUrl: 'https://images.unsplash.com/photo-1556740749-887f6717d7e4?auto=format&fit=crop&w=1200&q=80',
  },
];

export default function AdsPage() {
  const router = useRouter();
  const [ads, setAds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAds = async () => {
      try {
        const res = await fetch('/api/v1/ads');
        if (!res.ok) throw new Error('failed to fetch ads');
        const data = await res.json();
        setAds(data.items ?? MOCK_ADS);
      } catch (error) {
        setAds(MOCK_ADS);
      } finally {
        setLoading(false);
      }
    };

    fetchAds();
  }, []);

  return (
    <main className="min-h-screen bg-[#F8FAFC] px-4 py-4 text-[#111827]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">広告一覧</h1>
        <div className="rounded-[8px] bg-[#FFFFFF] px-3 py-2 text-sm shadow-sm ring-1 ring-slate-100">残高 1,240pt</div>
      </header>

      {loading ? (
        <p className="text-sm text-[#6B7280]" aria-busy="true">読み込み中...</p>
      ) : (
        <section className="space-y-3">
          {ads.map((ad) => (
            <AdCard key={ad.id} ad={ad} onStart={(id) => router.push(`/ads/${id}`)} />
          ))}
        </section>
      )}
    </main>
  );
}
