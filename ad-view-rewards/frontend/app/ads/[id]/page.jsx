'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import VideoPlayer from '../../../components/VideoPlayer';

const MOCK_AD_DETAIL = {
  id: 'ad-001',
  title: '新NISAの基本を30秒で解説',
  videoUrl: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
  thumbnailUrl: 'https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=1200&q=80',
};

export default function AdPlayerPage() {
  const router = useRouter();
  const params = useParams();
  const adId = params?.id;

  const [ad, setAd] = useState(null);
  const [elapsedSec, setElapsedSec] = useState(0);
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    if (!adId) return;

    const fetchAdDetail = async () => {
      try {
        const res = await fetch(`/api/v1/ads/${adId}`);
        if (!res.ok) throw new Error('failed to fetch ad detail');
        const data = await res.json();
        setAd(data);
      } catch (error) {
        setAd({ ...MOCK_AD_DETAIL, id: adId });
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
    } catch (error) {
      console.error('start API failed', error);
    }
  };

  const handleTimeUpdate = (event) => {
    setElapsedSec(event.currentTarget.currentTime || 0);
  };

  const handleComplete = async (id) => {
    setIsCompleting(true);
    try {
      await fetch(`/api/v1/ads/${id}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      router.push('/mypage');
    } catch (error) {
      console.error('complete API failed', error);
    } finally {
      setIsCompleting(false);
    }
  };

  if (!ad) {
    return (
      <main className="min-h-screen bg-[#F8FAFC] px-4 py-6">
        <p className="text-sm text-[#6B7280]">読み込み中...</p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#F8FAFC] px-4 py-4 text-[#111827]">
      <header className="mb-4 flex items-center justify-between">
        <button
          type="button"
          className="min-h-[44px] min-w-[44px] rounded-[8px] px-3 text-sm text-[#6B7280] hover:bg-slate-100"
          onClick={() => router.back()}
          aria-label="広告一覧へ戻る"
        >
          戻る
        </button>
        <p className="text-sm text-[#6B7280]">視聴セッション進行中</p>
      </header>

      <VideoPlayer
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
