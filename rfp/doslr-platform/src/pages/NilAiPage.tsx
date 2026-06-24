import { useCallback, useMemo, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import NilAiChat, { type ChatMessage } from "../components/nilai/NilAiChat";
import NilAiMap, { type NilAiMapHandle } from "../components/nilai/NilAiMap";
import { getParcelFeatures, resolveNilAiPrompt } from "../data/nilAiDemo";

const WELCOME_MESSAGE: ChatMessage = {
  id: "welcome",
  role: "assistant",
  content: [
    "Hello — I'm **NIL-AI**, wired to the DoSLR cadastral map.",
    "",
    "I can query parcels in different sectors of Puducherry or compile a cadastral analysis report with map layouts and attribute tables.",
    "",
    "Try asking about mutation-pending parcels, variance bands, or request a downloadable analysis report.",
  ].join("\n"),
};

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function NilAiPage() {
  const mapRef = useRef<NilAiMapHandle | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [isThinking, setIsThinking] = useState(false);
  const parcelFeatures = useMemo(() => getParcelFeatures("puducherry"), []);

  const handlePrompt = useCallback(
    (prompt: string) => {
      setMessages((prev) => [...prev, { id: makeId(), role: "user", content: prompt }]);
      setIsThinking(true);

      const thinkingDelay = 900 + Math.min(prompt.length * 12, 1400);

      window.setTimeout(() => {
        const result = resolveNilAiPrompt(prompt, parcelFeatures);

        if (result.parcelIds.length) {
          mapRef.current?.highlightParcels(result.parcelIds);
        } else {
          mapRef.current?.clearHighlights();
        }

        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: "assistant",
            content: result.reply,
            attachments: result.attachments,
          },
        ]);
        setIsThinking(false);
      }, thinkingDelay);
    },
    [parcelFeatures],
  );

  return (
    <div className="relative flex h-screen overflow-hidden bg-[#F7F7F5] p-3 text-[#1A1A1A] lg:p-4">
      <Link
        to="/app"
        className="absolute left-5 top-5 z-20 flex h-9 w-9 items-center justify-center rounded-lg border border-white/70 bg-white/90 text-slate-600 shadow-[0_8px_30px_rgba(0,0,0,0.06)] transition hover:bg-white hover:text-slate-900 lg:left-6 lg:top-6"
        aria-label="Back to workbench"
      >
        <ArrowLeft className="h-4 w-4" />
      </Link>

      <div className="mx-auto grid h-full w-full max-w-[1700px] min-h-0 gap-3 lg:grid-cols-[minmax(0,1.25fr)_minmax(320px,1fr)]">
        <NilAiMap ref={mapRef} />
        <NilAiChat messages={messages} isThinking={isThinking} onSubmit={handlePrompt} />
      </div>
    </div>
  );
}
