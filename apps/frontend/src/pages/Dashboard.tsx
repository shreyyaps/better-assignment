import { useEffect, useMemo, useRef, useState } from "react";

import { useStopTask, useStreamTask } from "@/hooks/taskHooks";
import { useAuthToken } from "@/hooks/useAuthToken";

type StreamEvent = { event: string; data: Record<string, unknown> };

type TaskItem = {
  id: number;
  prompt: string;
  status: string;
  created_at: string;
};

const Dashboard = () => {
  const [prompt, setPrompt] = useState("");
  const [events, setEvents] = useState<Record<number, StreamEvent[]>>({});
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<number | null>(null);
  const [activeTaskDetail, setActiveTaskDetail] = useState<Record<string, unknown> | null>(
    null
  );
  const streamMutation = useStreamTask();
  const stopMutation = useStopTask();
  const abortRef = useRef<AbortController | null>(null);
  const taskIdRef = useRef<number | null>(null);
  const { fetchToken } = useAuthToken();

  const activeEvents = useMemo(
    () => (activeTaskId ? events[activeTaskId] || [] : []),
    [activeTaskId, events]
  );

  const planSummary = useMemo(() => {
    const planEvent = activeEvents.find((ev) => ev.event === "plan");
    if (planEvent) {
      return String(planEvent.data.summary || "");
    }
    const stored = activeTaskDetail?.result as Record<string, unknown> | undefined;
    return String(stored?.plan_summary || "");
  }, [activeEvents, activeTaskDetail]);

  const latestResult = useMemo(() => {
    const complete = [...activeEvents].reverse().find((ev) => ev.event === "complete");
    if (complete) {
      return complete.data;
    }
    const error = [...activeEvents].reverse().find((ev) => ev.event === "error");
    if (error) {
      return error.data;
    }
    return (activeTaskDetail?.result as Record<string, unknown> | null) || null;
  }, [activeEvents, activeTaskDetail]);

  const liveStatus = useMemo(() => {
    if (activeEvents.length === 0) {
      return "idle";
    }
    const last = [...activeEvents].reverse()[0];
    const statusMap: Record<string, string> = {
      task: "started",
      plan: "planning",
      attempt_start: "running",
      step_start: "running",
      step_result: "running",
      replan: "replanning",
      step_error: "recovering",
      complete: "completed",
      error: "failed",
      stopped: "stopped",
    };
    return statusMap[last.event] || "running";
  }, [activeEvents]);

  const transcript = useMemo(() => {
    const messages: string[] = [];
    for (const ev of activeEvents) {
      if (ev.event === "plan") {
        messages.push(`Planned: ${String(ev.data.summary || "")}`);
      }
      if (ev.event === "attempt_start") {
        messages.push(`Attempt ${String(ev.data.attempt || "")} started.`);
      }
      if (ev.event === "step_start") {
        messages.push(`Step ${String(ev.data.index ?? "")} started.`);
      }
      if (ev.event === "step_result") {
        messages.push(`Step ${String(ev.data.index ?? "")} completed.`);
      }
      if (ev.event === "step_error") {
        messages.push(`Step ${String(ev.data.index ?? "")} failed: ${String(ev.data.error || "")}`);
      }
      if (ev.event === "replan") {
        messages.push("Replanned steps.");
      }
      if (ev.event === "stopped") {
        messages.push("Agent stopped by user.");
      }
      if (ev.event === "complete") {
        messages.push("Task completed.");
      }
      if (ev.event === "error") {
        messages.push(`Task failed: ${String(ev.data.error || "")}`);
      }
    }
    return messages;
  }, [activeEvents]);
  const failureShot = useMemo(() => {
    const err = [...activeEvents].reverse().find((ev) => ev.event === "step_error");
    if (!err) {
      return null;
    }
    return String(err.data.failure_screenshot_base64 || "");
  }, [activeEvents]);

  const loadTasks = async () => {
    const token = await fetchToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/tasks`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (response.ok) {
      const data = (await response.json()) as TaskItem[];
      setTasks(data);
      if (!activeTaskId && data.length > 0) {
        setActiveTaskId(data[0].id);
      }
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTaskDetail = async (taskId: number) => {
    const token = await fetchToken();
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/tasks/${taskId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (response.ok) {
      const data = (await response.json()) as Record<string, unknown>;
      setActiveTaskDetail(data);
    }
  };

  const handleRun = () => {
    if (!prompt.trim()) {
      return;
    }
    if (abortRef.current) {
      abortRef.current.abort();
    }
    const controller = new AbortController();
    abortRef.current = controller;
    streamMutation.mutate({
      prompt,
      signal: controller.signal,
      onEvent: (event) => {
        if (event.event === "task") {
          const taskId = Number((event.data as Record<string, unknown>).task_id);
          taskIdRef.current = taskId;
          setActiveTaskId(taskId);
          setActiveTaskDetail(null);
          setTasks((prev) => [
            { id: taskId, prompt, status: "running", created_at: new Date().toISOString() },
            ...prev,
          ]);
          setEvents((prev) => ({ ...prev, [taskId]: [event as StreamEvent] }));
          return;
        }
        if (!activeTaskId) {
          if (taskIdRef.current) {
            setActiveTaskId(taskIdRef.current);
            setActiveTaskDetail(null);
          } else {
            return;
          }
        }
        const currentId = taskIdRef.current ?? activeTaskId;
        if (!currentId) {
          return;
        }
        setEvents((prev) => ({
          ...prev,
          [currentId]: [...(prev[currentId] || []), event as StreamEvent],
        }));
        if (event.event === "complete" || event.event === "error") {
          loadTasks();
        }
      },
    });
  };

  const handleStop = () => {
    const id = taskIdRef.current ?? activeTaskId;
    if (!id) {
      return;
    }
    abortRef.current?.abort();
    stopMutation.mutate(id);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-[280px_1fr]">
      <aside className="border-r border-white/10 bg-black/30 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold">Chats</h2>
          <button className="text-xs text-white/60" onClick={loadTasks}>
            Refresh
          </button>
        </div>
        <div className="grid gap-3">
          {tasks.map((task) => (
            <button
              key={task.id}
              onClick={() => {
                setActiveTaskId(task.id);
                setActiveTaskDetail(null);
                loadTaskDetail(task.id);
              }}
              className={`text-left rounded-2xl border p-3 ${
                activeTaskId === task.id
                  ? "border-white/40 bg-white/10"
                  : "border-white/10 bg-white/5"
              }`}
            >
              <p className="text-sm text-white/80 line-clamp-2">{task.prompt}</p>
              <p className="text-xs text-white/40 mt-2">{task.status}</p>
            </button>
          ))}
        </div>
      </aside>

      <main className="px-8 py-10">
        <section className="card p-6 mb-6">
          <div className="flex flex-col gap-4">
            <div>
              <p className="text-white/60 text-sm">Objective</p>
              <h2 className="text-2xl font-display font-semibold">Browser Agent</h2>
            </div>
            <textarea
              className="min-h-[140px] rounded-2xl bg-white/5 border border-white/10 p-4 text-white"
              placeholder="Describe what the agent should do."
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
            />
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <button
                className="px-6 py-3 rounded-full bg-white/10 hover:bg-white/20"
                onClick={handleRun}
                disabled={streamMutation.isPending}
              >
                {streamMutation.isPending ? "Running..." : "Run Agent"}
              </button>
              <button
                className="px-6 py-3 rounded-full bg-white/10 hover:bg-white/20"
                onClick={handleStop}
                disabled={stopMutation.isPending || !activeTaskId}
              >
                Stop Agent
              </button>
              {streamMutation.isError && (
                <span className="text-red-300 text-sm">Stream failed. Check logs.</span>
              )}
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-white/60 text-sm mb-1">Live Status</p>
              <p className="text-white">{liveStatus}</p>
            </div>
          </div>
        </section>

        <section className="card p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Plan Summary</h3>
          {!planSummary && (
            <p className="text-white/60">Waiting for a plan...</p>
          )}
          {planSummary && (
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-white">{planSummary}</p>
            </div>
          )}
        </section>

        <section className="card p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Live Transcript</h3>
          {transcript.length === 0 && <p className="text-white/60">No updates yet.</p>}
          {transcript.length > 0 && (
            <div className="grid gap-2">
              {transcript.map((line, index) => (
                <div key={index} className="rounded-2xl border border-white/10 bg-white/5 p-3">
                  <p className="text-white/80 text-sm">{line}</p>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Latest Output</h3>
          {!latestResult && <p className="text-white/60">No output yet.</p>}
          {latestResult && (
            <div className="grid gap-4">
              {"feedback" in latestResult && (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-white/60 text-sm mb-2">Summary</p>
                  <p className="text-white">{String(latestResult.feedback || "")}</p>
                </div>
              )}
              {failureShot && (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-white/60 text-sm mb-2">Failure Screenshot</p>
                  <img
                    className="rounded-xl border border-white/10"
                    alt="Failure screenshot"
                    src={`data:image/png;base64,${failureShot}`}
                  />
                </div>
              )}
              {"screenshot_base64" in latestResult && (
                <img
                  className="rounded-2xl border border-white/10"
                  alt="Final screenshot"
                  src={`data:image/png;base64,${String(latestResult.screenshot_base64 || "")}`}
                />
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
