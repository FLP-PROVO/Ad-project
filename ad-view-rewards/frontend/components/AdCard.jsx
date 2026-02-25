'use client';

import React from 'react';

export default function AdCard({ ad, onStart }) {
  return (
    <article className="rounded-[8px] bg-[#FFFFFF] p-4 shadow-sm ring-1 ring-slate-100">
      <img
        src={ad.thumbnailUrl}
        alt={`${ad.brandName}の広告サムネイル`}
        className="aspect-video w-full rounded-[8px] object-cover"
      />

      <div className="mt-3">
        <h2 className="text-base font-semibold text-[#111827]">{ad.title}</h2>
        <p className="mt-1 text-sm text-[#6B7280]">{ad.brandName}</p>
      </div>

      <div className="mt-3 flex items-center justify-between">
        <p className="text-sm text-[#6B7280]">{ad.durationSec}秒</p>
        <span className="rounded-[8px] bg-emerald-50 px-2 py-1 text-sm font-semibold text-[#00C48C]">
          +{ad.rewardPoint}pt
        </span>
      </div>

      <button
        type="button"
        onClick={() => onStart(ad.id)}
        className="mt-4 h-10 min-h-[44px] w-full rounded-[8px] bg-[#0066FF] px-4 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#0066FF]"
        aria-label={`${ad.title}の視聴を開始`}
      >
        視聴を開始
      </button>
    </article>
  );
}
