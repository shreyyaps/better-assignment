import { create } from "zustand";

import { Email } from "@/features/emails/types";

type EmailState = {
  selectedEmail: Email | null;
  isReplyOpen: boolean;
  draftText: string;
  openReply: (email: Email, draft: string) => void;
  closeReply: () => void;
  setDraftText: (text: string) => void;
};

export const useEmailStore = create<EmailState>((set) => ({
  selectedEmail: null,
  isReplyOpen: false,
  draftText: "",
  openReply: (email, draft) =>
    set({ selectedEmail: email, isReplyOpen: true, draftText: draft }),
  closeReply: () => set({ selectedEmail: null, isReplyOpen: false, draftText: "" }),
  setDraftText: (text) => set({ draftText: text }),
}));
