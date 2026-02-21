import axios from "axios";

import { Task } from "@/features/tasks/types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8005",
});

const authHeaders = (token: string) => ({
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

export const runTask = async (token: string, prompt: string): Promise<Task> => {
  const response = await api.post<Task>("/tasks/run", { prompt }, authHeaders(token));
  return response.data;
};

export const streamTask = async (
  token: string,
  prompt: string,
  onEvent: (event: { event: string; data: unknown }) => void,
  signal?: AbortSignal
): Promise<void> => {
  const response = await fetch(`${api.defaults.baseURL}/tasks/stream`, {
    method: "POST",
    headers: {
      ...authHeaders(token).headers,
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({ prompt }),
    signal,
  });

  if (!response.body) {
    throw new Error("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      break;
    }
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const lines = raw.split("\n");
      let eventType = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) {
          eventType = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          data += line.slice(5).trim();
        }
      }
      if (data) {
        onEvent({ event: eventType, data: JSON.parse(data) });
      }
    }
  }
};

export const stopTask = async (token: string, taskId: number): Promise<void> => {
  await api.post(`/tasks/stop/${taskId}`, {}, authHeaders(token));
};
