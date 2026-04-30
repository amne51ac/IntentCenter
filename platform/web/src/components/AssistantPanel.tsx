import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { apiJson, apiSsePost } from "../api/client";
import {
  emptyThread,
  loadAssistantChats,
  saveAssistantChats,
  titleFromFirstUserMessage,
  type AssistantMsg,
  type AssistantThread,
} from "../lib/assistantChatsStorage";
import { ChatMarkdown } from "./ChatMarkdown";

type Suggestion = { id: string; label: string; prompt: string; kind?: string; skillId?: string };

type CopilotChatRes = { message: { role: string; content: string } };

const PANEL_WIDTH_STORAGE = "intentcenter.aiAssistant.widthPx";
const PANEL_W_MIN = 280;
const PANEL_W_DEFAULT = 384;

/** Composer grows with content up to this many lines, then scrolls. */
const ASSISTANT_COMPOSER_MAX_LINES = 8;

function clampWidth(px: number): number {
  if (typeof window === "undefined") return PANEL_W_DEFAULT;
  const cap = Math.min(800, Math.floor(window.innerWidth * 0.55));
  return Math.max(PANEL_W_MIN, Math.min(cap, Math.round(px)));
}

function readStoredWidth(): number {
  if (typeof window === "undefined") return PANEL_W_DEFAULT;
  const raw = localStorage.getItem(PANEL_WIDTH_STORAGE);
  if (raw) {
    const n = parseInt(raw, 10);
    if (!Number.isNaN(n)) return clampWidth(n);
  }
  return PANEL_W_DEFAULT;
}

type ChatStore = { threads: AssistantThread[]; activeId: string };

function pageContext(pathname: string): Record<string, string> {
  const m = pathname.match(/^\/o\/([^/]+)\/([^/]+)/);
  if (m) {
    return { route: pathname, resourceType: decodeURIComponent(m[1]), id: m[2] };
  }
  return { route: pathname };
}

function formatThreadTime(ts: number): string {
  try {
    return new Date(ts).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

async function errorTextFromResponse(res: Response): Promise<string> {
  let detail = res.statusText;
  try {
    const errBody: unknown = await res.json();
    if (errBody && typeof errBody === "object") {
      const o = errBody as Record<string, unknown>;
      if (typeof o.detail === "string") return o.detail;
      if (Array.isArray(o.detail)) {
        const parts = o.detail.map((x) =>
          typeof x === "object" && x && "msg" in x ? String((x as { msg: unknown }).msg) : String(x),
        );
        return parts.filter(Boolean).join("; ");
      }
      if (typeof o.error === "string") return o.error;
    }
  } catch {
    /* ignore */
  }
  return detail || `HTTP ${res.status}`;
}

type SseEvent = { type: string; text?: string; message?: string; done?: boolean };

/**
 * Read SSE/NDJSON from the response and invoke `onEvent` for each object.
 * `onEvent` may return a Promise; the parser **awaits** it so the caller can
 * `await` after each token (avoids React 18 batching an entire stream into one frame).
 */
function parseSseStream(
  res: Response,
  onEvent: (e: SseEvent) => void | Promise<void>,
): Promise<void> {
  if (!res.ok) {
    return errorTextFromResponse(res).then((t) => {
      throw new Error(t);
    });
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const dec = new TextDecoder();
  let buffer = "";
  return (async () => {
    let endSignal = false;
    const processLine = async (s: string) => {
      const t = s.replace(/^\uFEFF/, "").trim();
      if (!t) return;
      let raw: string;
      if (t.startsWith("data: ")) {
        raw = t.slice(6).trim();
      } else if (t.startsWith("data:")) {
        raw = t.slice(5).trimStart();
      } else if (t.startsWith("{") || t.startsWith("[")) {
        raw = t;
      } else {
        return;
      }
      if (raw === "[DONE]") {
        endSignal = true;
        return;
      }
      let parsed: Record<string, unknown> & SseEvent;
      try {
        parsed = JSON.parse(raw) as Record<string, unknown> & SseEvent;
      } catch {
        return;
      }
      if (parsed.error != null && parsed.type == null) {
        const er = parsed.error as { message?: string } | string;
        const msg =
          typeof er === "object" && er && typeof er.message === "string" ? er.message : String(parsed.error);
        await Promise.resolve(onEvent({ type: "error", message: msg }));
        return;
      }
      await Promise.resolve(onEvent(parsed as SseEvent));
    };
    for (;;) {
      const { done, value } = await reader.read();
      if (value) buffer += dec.decode(value, { stream: true });
      if (done) {
        for (const line of buffer.split("\n")) {
          await processLine(line);
          if (endSignal) return;
        }
        return;
      }
      const parts = buffer.split("\n");
      buffer = parts.pop() ?? "";
      for (const line of parts) {
        await processLine(line);
        if (endSignal) return;
      }
    }
  })();
}

export function AssistantPanel({ onMinimize }: { onMinimize: () => void }) {
  const loc = useLocation();
  const ctx = useMemo(() => pageContext(loc.pathname), [loc.pathname]);
  const [store, setStore] = useState<ChatStore>(() => loadAssistantChats());
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const [streamStatus, setStreamStatus] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [panelWidthPx, setPanelWidthPx] = useState(() => readStoredWidth());
  /** Bumps when an assistant run finishes so next-step suggestions refetch with the full new transcript. */
  const [nextStepsEpoch, setNextStepsEpoch] = useState(0);
  const queryClient = useQueryClient();
  const messagesForSuggestRef = useRef<AssistantMsg[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);
  const dragRef = useRef<{ startX: number; startW: number } | null>(null);
  const storeRef = useRef(store);
  storeRef.current = store;

  const messages = useMemo(
    () => store.threads.find((t) => t.id === store.activeId)?.messages ?? [],
    [store.threads, store.activeId],
  );

  messagesForSuggestRef.current = messages;

  const nextSteps = useQuery({
    /* Transcript for API must match the ref below; `nextStepsEpoch` is bumped after each completed turn. */
    queryKey: [
      "copilot",
      "suggest_next_steps",
      loc.pathname,
      store.activeId,
      nextStepsEpoch,
    ] as const,
    queryFn: () =>
      apiJson<{ suggestions: Suggestion[] }>("/v1/copilot/suggest_next_steps", {
        method: "POST",
        body: JSON.stringify({
          context: ctx,
          messages: messagesForSuggestRef.current,
        }),
      }),
    enabled: !pending,
    staleTime: 0,
  });

  useEffect(() => {
    saveAssistantChats(store.threads, store.activeId);
  }, [store.threads, store.activeId]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, pending, store.activeId, streamStatus]);

  const sizeAssistantComposer = useCallback(() => {
    const el = composerRef.current;
    if (!el) return;
    const cs = getComputedStyle(el);
    const lhRaw = cs.lineHeight;
    const fontSize = parseFloat(cs.fontSize) || 14;
    const lineH =
      lhRaw === "normal" || !parseFloat(lhRaw) ? fontSize * 1.4 : Math.max(1, parseFloat(lhRaw) || fontSize * 1.4);
    const padY = (parseFloat(cs.paddingTop) || 0) + (parseFloat(cs.paddingBottom) || 0);
    const maxPx = lineH * ASSISTANT_COMPOSER_MAX_LINES + padY;
    el.style.height = "auto";
    const sh = el.scrollHeight;
    el.style.height = `${Math.min(sh, maxPx)}px`;
    el.style.overflowY = sh > maxPx + 0.5 ? "auto" : "hidden";
  }, []);

  useLayoutEffect(() => {
    sizeAssistantComposer();
  }, [input, panelWidthPx, sizeAssistantComposer]);

  const runAssistant = useCallback(
    async (userText: string) => {
      const tid = storeRef.current.activeId;
      const thread = storeRef.current.threads.find((t) => t.id === tid);
      if (!thread) return;
      const wasEmpty = thread.messages.length === 0;
      setErr(null);
      setStreamStatus(null);
      setPending(true);
      const withUser = [...thread.messages, { role: "user" as const, content: userText }];
      const withAssistant: AssistantThread["messages"] = [
        ...withUser,
        { role: "assistant" as const, content: "" },
      ];
      setStore((s) => ({
        ...s,
        threads: s.threads.map((t) => (t.id === tid ? { ...t, messages: withAssistant, updatedAt: Date.now() } : t)),
      }));

      let acc = "";
      /** Synchronous copy of the thread to POST to suggest_next_steps (React state can lag the last stream chunk). */
      let nextStepsTranscript: AssistantMsg[] = withUser;
      const payload = {
        messages: withUser.map((m) => ({ role: m.role, content: m.content })),
        context: ctx,
      };

      try {
        const res = await apiSsePost("/v1/copilot/chat/stream", payload);
        await parseSseStream(res, async (ev) => {
          if (ev.type === "delta" && typeof ev.text === "string") {
            acc += ev.text;
            setStreamStatus(null);
            setStore((s) => ({
              ...s,
              threads: s.threads.map((t) => {
                if (t.id !== tid) return t;
                return {
                  ...t,
                  messages: [
                    ...withUser,
                    { role: "assistant" as const, content: acc },
                  ],
                  updatedAt: Date.now(),
                };
              }),
            }));
            // Yield the main thread so React paints between tokens (React 18+ batches sync updates in one frame).
            await new Promise<void>((r) => setTimeout(r, 0));
          } else if (ev.type === "status" && typeof ev.text === "string") {
            setStreamStatus(ev.text);
          } else if (ev.type === "error") {
            throw new Error(String(ev.message || "Request failed"));
          }
        });
        let finalText = acc;
        if (!finalText.trim()) {
          try {
            const fb = await apiJson<CopilotChatRes>("/v1/copilot/chat", {
              method: "POST",
              body: JSON.stringify(payload),
            });
            const t = (fb.message?.content ?? "").trim();
            if (t) {
              finalText = t;
              setStore((s) => ({
                ...s,
                threads: s.threads.map((tt) =>
                  tt.id === tid
                    ? {
                        ...tt,
                        messages: [...withUser, { role: "assistant" as const, content: t }],
                        updatedAt: Date.now(),
                      }
                    : tt,
                ),
              }));
            }
          } catch {
            /* non-stream fallback failed */
          }
        }
        if (!finalText.trim()) {
          setErr("The assistant returned no text. Check the LLM model, proxy, and API key in Admin → LLM.");
          setStore((s) => ({
            ...s,
            threads: s.threads.map((t) => (t.id === tid ? { ...t, messages: withUser, updatedAt: Date.now() } : t)),
          }));
        }
        if (wasEmpty && finalText.trim()) {
          const firstUser = withUser[0]!.content;
          void (async () => {
            try {
              const r = await apiJson<{ title: string | null }>("/v1/copilot/suggest_thread_title", {
                method: "POST",
                body: JSON.stringify({ userMessage: firstUser, assistantMessage: finalText }),
              });
              const raw = (r.title || "").trim();
              setStore((s) => ({
                ...s,
                threads: s.threads.map((t) => {
                  if (t.id !== tid) return t;
                  if (raw) {
                    return { ...t, title: raw.length > 80 ? raw.slice(0, 77) + "…" : raw, updatedAt: Date.now() };
                  }
                  return { ...t, title: titleFromFirstUserMessage(firstUser), updatedAt: Date.now() };
                }),
              }));
            } catch {
              setStore((s) => ({
                ...s,
                threads: s.threads.map((t) =>
                  t.id === tid
                    ? { ...t, title: titleFromFirstUserMessage(firstUser), updatedAt: Date.now() }
                    : t,
                ),
              }));
            }
          })();
        }
        nextStepsTranscript =
          finalText.trim().length > 0
            ? [...withUser, { role: "assistant" as const, content: finalText }]
            : withUser;
      } catch (e) {
        setErr(e instanceof Error ? e.message : "Request failed");
        setStore((s) => ({
          ...s,
          threads: s.threads.map((t) => (t.id === tid ? { ...t, messages: withUser, updatedAt: Date.now() } : t)),
        }));
        nextStepsTranscript = withUser;
      } finally {
        messagesForSuggestRef.current = nextStepsTranscript;
        setPending(false);
        setStreamStatus(null);
        setNextStepsEpoch((e) => e + 1);
        // Ref is correct immediately; state may not have committed yet. Force refetch so POST uses the snapshot above.
        queueMicrotask(() => {
          void queryClient.invalidateQueries({ queryKey: ["copilot", "suggest_next_steps"] });
        });
      }
    },
    [ctx, queryClient],
  );

  const onNewChat = useCallback(() => {
    setErr(null);
    const t = emptyThread();
    setStore((s) => ({ threads: [t, ...s.threads], activeId: t.id }));
  }, []);

  const onSelectThread = useCallback((id: string) => {
    if (id === storeRef.current.activeId) return;
    setErr(null);
    setStore((s) => ({ ...s, activeId: id }));
  }, []);

  const onDeleteThread = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("Delete this conversation? This cannot be undone.")) return;
    setStore((s) => {
      const threads = s.threads.filter((t) => t.id !== id);
      if (threads.length === 0) {
        const t = emptyThread();
        return { threads: [t], activeId: t.id };
      }
      const activeId = s.activeId === id ? threads[0]!.id : s.activeId;
      return { threads, activeId };
    });
  }, []);

  const onSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const t = input.trim();
      if (!t || pending) return;
      setInput("");
      void runAssistant(t);
    },
    [input, pending, runAssistant],
  );

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const t = input.trim();
      if (!t || pending) return;
      setInput("");
      void runAssistant(t);
    }
  };

  const onResizePointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return;
    e.preventDefault();
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
    dragRef.current = { startX: e.clientX, startW: panelWidthPx };
  };

  const onResizePointerMove = (e: React.PointerEvent) => {
    const d = dragRef.current;
    if (!d) return;
    const deltaX = e.clientX - d.startX;
    setPanelWidthPx(clampWidth(d.startW - deltaX));
  };

  const onResizePointerUp = (e: React.PointerEvent) => {
    if (!dragRef.current) return;
    dragRef.current = null;
    try {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      /* not captured */
    }
    setPanelWidthPx((w) => {
      const c = clampWidth(w);
      localStorage.setItem(PANEL_WIDTH_STORAGE, String(c));
      return c;
    });
  };

  useEffect(() => {
    const onWin = () => setPanelWidthPx((w) => clampWidth(w));
    window.addEventListener("resize", onWin);
    return () => window.removeEventListener("resize", onWin);
  }, []);

  const sortedForList = useMemo(() => [...store.threads].sort((a, b) => b.updatedAt - a.updatedAt), [store.threads]);

  const activeThreadIsEmpty = messages.length === 0;

  const onObjectContext = ctx.resourceType && ctx.id;
  const nextSuggestions = nextSteps.data?.suggestions;
  // Show whenever we have suggestions. Do not gate on isLoading: it can block chips during some refetch paths.
  const showNextSteps =
    !nextSteps.isError && Array.isArray(nextSuggestions) && nextSuggestions.length > 0;

  return (
    <aside
      className="ai-assistant-panel"
      role="dialog"
      aria-label="AI assistant"
      style={{ width: panelWidthPx }}
    >
      <div
        className="ai-assistant-resize-handle"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize AI assistant panel. Drag left or right."
        tabIndex={0}
        onPointerDown={onResizePointerDown}
        onPointerMove={onResizePointerMove}
        onPointerUp={onResizePointerUp}
        onPointerCancel={onResizePointerUp}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
            e.preventDefault();
            setPanelWidthPx((w) => {
              const next = clampWidth(w + (e.key === "ArrowLeft" ? 8 : -8));
              localStorage.setItem(PANEL_WIDTH_STORAGE, String(next));
              return next;
            });
          }
        }}
      />
      <div className="ai-assistant-panel-body">
        <div className="ai-assistant-panel-header">
          <h2 className="ai-assistant-title">AI assistant</h2>
          <div className="ai-assistant-header-actions">
            <button
              type="button"
              className="btn-text"
              onClick={onNewChat}
              disabled={activeThreadIsEmpty}
              title={
                activeThreadIsEmpty
                  ? "This conversation is still empty — send a message first"
                  : "Start a new conversation"
              }
            >
              New chat
            </button>
            <button type="button" className="btn-text" onClick={onMinimize} aria-label="Minimize">
              Minimize
            </button>
          </div>
        </div>

        <details className="ai-assistant-chats-details">
          <summary className="ai-assistant-chats-summary">
            <span>Conversations</span>
            <span className="ai-assistant-chats-count">({store.threads.length})</span>
          </summary>
          <ul className="ai-assistant-thread-list" role="list">
            {sortedForList.map((t) => {
              const active = t.id === store.activeId;
              return (
                <li key={t.id} className={"ai-assistant-thread-item" + (active ? " ai-assistant-thread-item--active" : "")}>
                  <button
                    type="button"
                    className="ai-assistant-thread-select"
                    onClick={() => onSelectThread(t.id)}
                    title={t.title}
                    aria-current={active ? "true" : undefined}
                  >
                    <span className="ai-assistant-thread-title">{t.title || "New chat"}</span>
                    <span className="ai-assistant-thread-meta">
                      {t.messages.length} {t.messages.length === 1 ? "message" : "messages"} ·{" "}
                      {formatThreadTime(t.updatedAt)}
                    </span>
                  </button>
                  <button
                    type="button"
                    className="ai-assistant-thread-delete"
                    onClick={(e) => onDeleteThread(t.id, e)}
                    aria-label={"Delete " + t.title}
                    title="Delete conversation"
                  >
                    ×
                  </button>
                </li>
              );
            })}
          </ul>
        </details>

        {onObjectContext ? (
          <p className="ai-assistant-context">
            <span className="ai-assistant-context-label">Viewing</span> {ctx.resourceType}
            <span className="ai-assistant-context-sep">·</span>
            <code className="ai-assistant-context-id" title={ctx.id}>
              {ctx.id.length > 14 ? ctx.id.slice(0, 8) + "…" + ctx.id.slice(-4) : ctx.id}
            </code>
          </p>
        ) : null}

        <div className="ai-assistant-messages" ref={scrollRef} aria-live="polite">
          {messages.length === 0 && !pending ? (
            <p className="ai-assistant-welcome">Ask a question or describe what you want to find in the inventory.</p>
          ) : null}
          {messages.map((m, i) => {
            const last = i === messages.length - 1;
            const emptyWait = m.role === "assistant" && !m.content && pending && last;
            return (
              <div key={i} className={"ai-assistant-msg ai-assistant-msg-" + m.role}>
                <span className="ai-assistant-msg-role">{m.role === "user" ? "You" : "Assistant"}</span>
                <div className={"ai-assistant-msg-body" + (m.role === "assistant" ? " ai-assistant-msg-body--md" : "")}>
                  {m.role === "user" ? (
                    <ChatMarkdown text={m.content} variant="user" />
                  ) : m.content ? (
                    <ChatMarkdown text={m.content} />
                  ) : emptyWait ? (
                    streamStatus ? (
                      <span className="muted ai-assistant-status-inline">{streamStatus}</span>
                    ) : (
                      <div className="ai-assistant-thinking ai-assistant-thinking--inline" aria-live="polite" aria-busy>
                        <span className="ai-assistant-thinking-label">Thinking</span>
                        <span className="ai-assistant-thinking-dots" aria-hidden>
                          <span className="ai-assistant-dot" />
                          <span className="ai-assistant-dot" />
                          <span className="ai-assistant-dot" />
                        </span>
                      </div>
                    )
                  ) : null}
                </div>
              </div>
            );
          })}
          {err ? <p className="error-text">{err}</p> : null}
        </div>

        {showNextSteps ? (
          <div className="ai-assistant-next-steps" role="region" aria-label="Suggested next steps">
            <div className="ai-assistant-next-steps-heading">Next steps</div>
            <p className="ai-assistant-next-steps-hint muted">Based on this page and your chat</p>
            <div className="ai-assistant-next-step-chips" role="group" aria-label="LLM next step options">
              {nextSuggestions.map((s) => (
                <button
                  key={`${s.id}-${nextStepsEpoch}`}
                  type="button"
                  className="ai-assistant-chip ai-assistant-chip--next"
                  onClick={() => {
                    if (pending) return;
                    setInput("");
                    void runAssistant(s.prompt);
                  }}
                  disabled={pending}
                  title={s.prompt}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <form onSubmit={onSubmit} className="ai-assistant-form">
          <div className="ai-assistant-composer">
            <textarea
              ref={composerRef}
              className="input ai-assistant-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              rows={1}
              placeholder="Message the assistant…"
              disabled={pending}
            />
            <div className="ai-assistant-composer-actions">
              <span className="ai-assistant-hint">Enter to send · Shift+Enter for newline</span>
              <button type="submit" className="btn btn-primary" disabled={pending || !input.trim()}>
                Send
              </button>
            </div>
          </div>
        </form>
      </div>
    </aside>
  );
}
