import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Loader2, Map, Send, Sparkles, User } from "lucide-react";
import NilAiDownloadCard from "./NilAiDownloadCard";
import type { NilAiAttachment } from "../../lib/nilAiExport";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  attachments?: NilAiAttachment[];
};

type Props = {
  messages: ChatMessage[];
  isThinking: boolean;
  onSubmit: (prompt: string) => void;
};

function renderMarkdownLite(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-semibold text-slate-900">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={index} className="italic text-slate-700">
          {part.slice(1, -1)}
        </em>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

export default function NilAiChat({ messages, isThinking, onSubmit }: Props) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const value = draft.trim();
    if (!value || isThinking) return;
    setDraft("");
    onSubmit(value);
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-white/70 bg-white shadow-[0_8px_30px_rgba(0,0,0,0.06)]">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3">
        <Sparkles className="h-4 w-4 text-slate-600" />
        <div>
          <h2 className="text-sm font-semibold text-[#1A1A1A]">NIL-AI</h2>
          <p className="text-[11px] text-slate-500">Cadastral intelligence</p>
        </div>
      </div>

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-2.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.role === "assistant" && (
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
                <Map className="h-3.5 w-3.5" />
              </div>
            )}
            <div
              className={`max-w-[92%] space-y-2 ${message.role === "user" ? "" : ""}`}
            >
              <div
                className={`rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed ${
                  message.role === "user"
                    ? "bg-slate-900 text-white"
                    : "border border-slate-100 bg-slate-50 text-slate-700"
                }`}
              >
                {message.role === "assistant" ? (
                  <div className="whitespace-pre-wrap">{renderMarkdownLite(message.content)}</div>
                ) : (
                  message.content
                )}
              </div>
              {message.attachments?.length ? (
                <div className="space-y-2">
                  {message.attachments.map((attachment) => (
                    <NilAiDownloadCard key={attachment.id} attachment={attachment} />
                  ))}
                </div>
              ) : null}
            </div>
            {message.role === "user" && (
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
                <User className="h-3.5 w-3.5" />
              </div>
            )}
          </div>
        ))}

        {isThinking && (
          <div className="flex gap-2.5">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-slate-600">
              <Map className="h-3.5 w-3.5" />
            </div>
            <div className="flex items-center gap-2 rounded-2xl border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-[13px] text-slate-500">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Analysing cadastral index…
            </div>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-100 p-3">
        <div className="flex items-end gap-2 rounded-xl border border-slate-200 bg-slate-50/80 p-2 focus-within:border-slate-300 focus-within:ring-2 focus-within:ring-slate-100">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSubmit(event);
              }
            }}
            rows={2}
            placeholder="Ask NIL-AI to query parcels or generate a report…"
            className="min-h-[44px] flex-1 resize-none bg-transparent px-2 py-1.5 text-sm text-slate-800 outline-none placeholder:text-slate-400"
          />
          <button
            type="submit"
            disabled={!draft.trim() || isThinking}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#1A1A1A] text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
            aria-label="Send prompt"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
