import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  fetchEmailCount,
  fetchEmails,
  generateReply,
  sendReply,
  syncEmails,
  unsubscribeEmail,
} from "@/api/emailApi";
import { useAuthToken } from "@/hooks/useAuthToken";

export const useEmails = () => {
  const { fetchToken } = useAuthToken();
  return useQuery({
    queryKey: ["emails"],
    queryFn: async () => fetchEmails(await fetchToken()),
  });
};

export const useEmailCount = () => {
  const { fetchToken } = useAuthToken();
  return useQuery({
    queryKey: ["emails", "count"],
    queryFn: async () => fetchEmailCount(await fetchToken()),
  });
};

export const useSyncEmails = () => {
  const queryClient = useQueryClient();
  const { fetchToken } = useAuthToken();

  return useMutation({
    mutationFn: async () => syncEmails(await fetchToken()),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      queryClient.invalidateQueries({ queryKey: ["emails", "count"] });
    },
  });
};

export const useGenerateReply = () => {
  const { fetchToken } = useAuthToken();
  return useMutation({
    mutationFn: async (emailId: number) => generateReply(await fetchToken(), emailId),
  });
};

export const useSendReply = () => {
  const { fetchToken } = useAuthToken();
  return useMutation({
    mutationFn: async ({ emailId, replyText }: { emailId: number; replyText: string }) =>
      sendReply(await fetchToken(), emailId, replyText),
  });
};

export const useUnsubscribe = () => {
  const queryClient = useQueryClient();
  const { fetchToken } = useAuthToken();

  return useMutation({
    mutationFn: async (emailId: number) => unsubscribeEmail(await fetchToken(), emailId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["emails"] });
    },
  });
};
