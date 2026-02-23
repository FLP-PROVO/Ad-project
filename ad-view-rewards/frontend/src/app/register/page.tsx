'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '@/lib/api';
import { setToken } from '@/lib/auth';
import { TokenResponse } from '@/lib/types';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [error, setError] = useState('');

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError('');

    try {
      const payload = await apiFetch<TokenResponse>('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          phone_number: phoneNumber || null,
        }),
      });
      setToken(payload.access_token);
      router.push('/ads');
    } catch (e) {
      setError(e instanceof Error ? e.message : '登録に失敗しました');
    }
  }

  return (
    <section className="card">
      <h1>新規登録</h1>
      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="email">Email</label><br />
          <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div>
          <label htmlFor="password">Password</label><br />
          <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </div>
        <div>
          <label htmlFor="phone">Phone (optional)</label><br />
          <input id="phone" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} />
        </div>
        <button type="submit">登録する</button>
      </form>
      {error && <p className="error">{error}</p>}
    </section>
  );
}
