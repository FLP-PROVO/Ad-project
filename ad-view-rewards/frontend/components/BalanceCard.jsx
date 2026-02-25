'use client';

import React from 'react';

export default function BalanceCard({ totalPoint, updatedAt }) {
  return (
    <section className="rounded-[8px] bg-[#FFFFFF] p-4 shadow-sm ring-1 ring-slate-100">
      <p className="text-sm text-[#6B7280]">現在の残高</p>
      <p className="mt-1 text-3xl font-bold text-[#111827]">{Number(totalPoint).toLocaleString()}pt</p>
      <p className="mt-2 text-xs text-[#6B7280]">最終更新: {updatedAt}</p>
    </section>
  );
}
