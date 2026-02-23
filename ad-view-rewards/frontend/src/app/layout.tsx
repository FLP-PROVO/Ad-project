import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Ad View Rewards Frontend',
  description: 'Minimal viewer flow frontend for Ad View Rewards',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <nav>
          <ul>
            <li><Link href="/register">register</Link></li>
            <li><Link href="/login">login</Link></li>
            <li><Link href="/ads">ads</Link></li>
            <li><Link href="/profile">profile</Link></li>
          </ul>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
