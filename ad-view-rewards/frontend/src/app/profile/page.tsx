'use client';

import { useEffect, useState } from 'react';
import { apiFetch } from '@/lib/api';
import { BalanceRead, LedgerPageRead } from '@/lib/types';

export default function ProfilePage() {
  const [balance, setBalance] = useState<number | null>(null);
  const [ledger, setLedger] = useState<LedgerPageRead | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const balanceRes = await apiFetch<BalanceRead>('/api/v1/users/me/balance', {}, true);
        const ledgerRes = await apiFetch<LedgerPageRead>('/api/v1/users/me/ledger?page=1&limit=20', {}, true);
        setBalance(balanceRes.balance);
        setLedger(ledgerRes);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'プロフィールの取得に失敗しました');
      }
    };

    void loadProfile();
  }, []);

  return (
    <section>
      <h1>プロフィール</h1>
      {error && <p className="error">{error}</p>}
      <article className="card">
        <h2>現在の残高</h2>
        <p>{balance ?? 0} pt</p>
      </article>
      <article className="card">
        <h2>ポイント台帳</h2>
        {!ledger?.items.length && <p>台帳エントリはありません。</p>}
        <ul>
          {ledger?.items.map((item) => (
            <li key={item.id}>
              {new Date(item.created_at).toLocaleString()} / {item.reason} / {item.change > 0 ? '+' : ''}
              {item.change}
            </li>
          ))}
        </ul>
      </article>
    </section>
  );
}
