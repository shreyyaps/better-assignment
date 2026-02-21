export type Task = {
  id: number;
  prompt: string;
  status: string;
  result?: Record<string, unknown> | null;
  error?: string | null;
  created_at: string;
  updated_at: string;
};
