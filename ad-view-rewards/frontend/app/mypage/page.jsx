'use client';

import React, { useEffect, useState } from 'react';
import BalanceCard from '../../components/BalanceCard';

const MOCK_WALLET = {
  totalPoint: 1240,
  updatedAt: '2026-02-25 10:00',
};

const MOCK_HISTORY = [
  { id: 'h1', type: '広告視聴', point: 30, createdAt: '2026-02-25 09:30', status: '付与済み' },
  { id: 'h2', type: '広告視聴', point: 45, createdAt: '2026-02-24 20:12', status: '付与済み' },
];

export default function MyPage() {
  const [wallet, setWallet] = useState(MOCK_WALLET);
  const [history, setHistory] = useState(MOCK_HISTORY);

  useEffect(() => {
    const fetchMyPageData = async () => {
      try {
        const [walletRes, historyRes] = await Promise.all([
          fetch('/api/v1/wallet'),
          fetch('/api/v1/rewards/history?period=30d'),
        ]);

        const walletJson = walletRes.ok ? await walletRes.json() : MOCK_WALLET;
        const historyJson = historyRes.ok ? await historyRes.json() : { items: MOCK_HISTORY };

        setWallet({
          totalPoint: walletJson.totalPoint ?? MOCK_WALLET.totalPoint,
          updatedAt: walletJson.updatedAt ?? MOCK_WALLET.updatedAt,
        });
        setHistory(historyJson.items ?? MOCK_HISTORY);
      } catch (error) {
        setWallet(MOCK_WALLET);
        setHistory(MOCK_HISTORY);
      }
    };

    fetchMyPageData();
  }, []);

  return (
    <main className="min-h-screen bg-[#F8FAFC] px-4 py-4 text-[#111827]">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">マイページ</h1>
        <button
          type="button"
          className="min-h-[44px] min-w-[44px] rounded-[8px] px-3 text-sm text-[#6B7280] hover:bg-slate-100"
        >
          設定
        </button>
      </header>

      <div className="space-y-4">
        <BalanceCard totalPoint={wallet.totalPoint} updatedAt={wallet.updatedAt} />

        <section className="rounded-[8px] bg-[#FFFFFF] p-4 shadow-sm ring-1 ring-slate-100">
          <h2 className="mb-2 text-base font-semibold text-[#111827]">履歴</h2>

          {history.length === 0 ? (
            <p className="text-sm text-[#6B7280]">まだ履歴がありません。</p>
          ) : (
            <ul className="divide-y divide-slate-100">
              {history.map((item) => (
                <li key={item.id} className="flex min-h-[56px] items-center justify-between py-3">
                  <div>
                    <p className="text-sm text-[#111827]">{item.type}</p>
                    <p className="text-xs text-[#6B7280]">{item.createdAt}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-[#00C48C]">+{item.point}pt</p>
                    <p className="text-xs text-[#6B7280]">{item.status}</p>
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
