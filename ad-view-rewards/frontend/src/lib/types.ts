export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type Ad = {
  id: string;
  title: string;
  video_url: string;
  reward_point: number;
  remaining_budget: number;
  is_active: boolean;
};

export type AdView = {
  id: string;
  ad_id: string;
  completed: boolean;
  reward_granted: boolean;
  started_at: string;
  completed_at: string | null;
};

export type BalanceRead = {
  balance: number;
};

export type LedgerEntry = {
  id: string;
  change: number;
  reason: string;
  reference_id: string | null;
  created_at: string;
};

export type LedgerPageRead = {
  page: number;
  limit: number;
  total: number;
  items: LedgerEntry[];
};
