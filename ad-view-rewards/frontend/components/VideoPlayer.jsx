'use client';

import React, { useMemo } from 'react';

export default function VideoPlayer({
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
  const progressPercent = useMemo(() => {
    const value = Math.min(100, Math.floor((elapsedSec / requiredSec) * 100));
    return Number.isFinite(value) ? value : 0;
  }, [elapsedSec, requiredSec]);

  const canComplete = elapsedSec >= requiredSec;

  return (
    <section className="space-y-4">
      <div className="overflow-hidden rounded-[8px] bg-black">
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

      <div className="rounded-[8px] bg-[#FFFFFF] p-4 shadow-sm ring-1 ring-slate-100" aria-live="polite">
        <p className="text-sm text-[#111827]">視聴 {Math.floor(elapsedSec)} / {requiredSec} 秒</p>
        <div
          className="mt-2 h-2 w-full rounded-full bg-slate-200"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={requiredSec}
          aria-valuenow={Math.floor(elapsedSec)}
        >
          <div
            className={`h-2 rounded-full ${canComplete ? 'bg-[#00C48C]' : 'bg-[#0066FF]'}`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="rounded-[8px] bg-[#FFFFFF] p-4 shadow-sm ring-1 ring-slate-100">
        <p className="text-sm text-[#6B7280]">獲得予定</p>
        <p className="mt-1 text-2xl font-bold text-[#00C48C]">+30pt</p>
        <p className="mt-1 text-xs text-[#6B7280]">15秒以上の視聴で受け取り可能</p>
      </div>

      <button
        type="button"
        disabled={!canComplete || isCompleting}
        onClick={() => onComplete(adId)}
        className="h-10 min-h-[44px] w-full rounded-[8px] bg-[#00C48C] px-4 text-sm font-semibold text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:bg-emerald-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#00C48C]"
      >
        {isCompleting ? '処理中...' : '報酬を受け取る'}
      </button>
    </section>
  );
}
