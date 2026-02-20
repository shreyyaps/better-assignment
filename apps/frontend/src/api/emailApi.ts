import axios from "axios";

import { Email, EmailCount, ReplyDraft } from "@/features/emails/types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

const authHeaders = (token: string) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

export const fetchEmails = async (token: string): Promise<Email[]> => {
  const response = await api.get<Email[]>("/emails", authHeaders(token));
  return response.data;
};

export const fetchEmailCount = async (token: string): Promise<EmailCount> => {
  const response = await api.get<EmailCount>("/emails/count", authHeaders(token));
  return response.data;
};

export const syncEmails = async (token: string): Promise<{ synced: number }> => {
  const response = await api.post<{ synced: number }>("/emails/sync", {}, authHeaders(token));
  return response.data;
};

export const generateReply = async (
  token: string,
  emailId: number
): Promise<ReplyDraft> => {
  const response = await api.post<ReplyDraft>(
    "/emails/reply",
    { email_id: emailId },
    authHeaders(token)
  );
  return response.data;
};

export const sendReply = async (
  token: string,
  emailId: number,
  replyText: string
): Promise<ReplyDraft> => {
  const response = await api.post<ReplyDraft>(
    "/emails/send",
    { email_id: emailId, reply_text: replyText },
    authHeaders(token)
  );
  return response.data;
};

export const unsubscribeEmail = async (
  token: string,
  emailId: number
): Promise<{ email_id: number; unsubscribed: boolean }> => {
  const response = await api.post<{ email_id: number; unsubscribed: boolean }>(
    "/emails/unsubscribe",
    { email_id: emailId },
    authHeaders(token)
  );
  return response.data;
};
