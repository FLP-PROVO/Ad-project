import { test, expect } from '@playwright/test';

test('viewer flow skeleton', async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: 'ログイン' })).toBeVisible();

  // NOTE:
  // 実運用ではここで register/login API モック or テスト用バックエンドを使い、
  // /ads -> /ads/[id] -> /profile の一連動作を検証する。
});
