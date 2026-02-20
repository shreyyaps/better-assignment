export type Importance = "high" | "medium" | "low";

export type Email = {
  id: number;
  gmail_message_id: string;
  subject: string | null;
  sender: string | null;
  snippet: string | null;
  body: string | null;
  importance: Importance;
  is_spam: boolean;
  unsubscribed: boolean;
  created_at: string;
};
