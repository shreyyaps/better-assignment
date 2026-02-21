import { useMutation } from "@tanstack/react-query";

import { runTask, stopTask, streamTask } from "@/api/taskApi";
import { useAuthToken } from "@/hooks/useAuthToken";

export const useRunTask = () => {
  const { fetchToken } = useAuthToken();

  return useMutation({
    mutationFn: async (prompt: string) => runTask(await fetchToken(), prompt),
  });
};

export const useStreamTask = () => {
  const { fetchToken } = useAuthToken();

  return useMutation({
    mutationFn: async (payload: {
      prompt: string;
      onEvent: (event: { event: string; data: unknown }) => void;
      signal?: AbortSignal;
    }) => streamTask(await fetchToken(), payload.prompt, payload.onEvent, payload.signal),
  });
};

export const useStopTask = () => {
  const { fetchToken } = useAuthToken();

  return useMutation({
    mutationFn: async (taskId: number) => stopTask(await fetchToken(), taskId),
  });
};
