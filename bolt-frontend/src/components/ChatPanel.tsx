import { useEffect, useRef, useState } from 'react';
import { Loader2, MessageCircle, Send, Sparkles, X } from 'lucide-react';
import { api } from '@/lib/api';
import type { ChatSource } from '@/types';

interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  sources?: ChatSource[];
  isError?: boolean;
}

const SUGGESTIONS = [
  'Which of my values are out of range?',
  'Explain my results in simple words',
  'What should I ask my doctor?',
];

// The AI sometimes answers with markdown; show it as clean plain text.
function cleanText(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/^[ \t]*[*-][ \t]+/gm, '• ')
    .trim();
}

export function ChatPanel({ reportId }: { reportId: number }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [searchAll, setSearchAll] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const nextId = useRef(1);
  const alive = useRef(true);

  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending, open]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || sending) return;

    setMessages((m) => [...m, { id: nextId.current++, role: 'user', text: question }]);
    setInput('');
    setSending(true);

    try {
      const res = await api.chat(reportId, question, searchAll);
      if (!alive.current) return;
      setMessages((m) => [
        ...m,
        { id: nextId.current++, role: 'assistant', text: res.answer, sources: res.sources },
      ]);
    } catch (e) {
      if (!alive.current) return;
      setMessages((m) => [
        ...m,
        {
          id: nextId.current++,
          role: 'assistant',
          isError: true,
          text: e instanceof Error ? e.message : 'Something went wrong. Please try again.',
        },
      ]);
    } finally {
      if (alive.current) setSending(false);
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full px-5 py-3 text-white font-medium shadow-lg transition-transform hover:scale-105"
        style={{ background: 'var(--teal)' }}
        aria-label="Open AI chat assistant"
      >
        <MessageCircle size={20} />
        Ask AI
      </button>
    );
  }

  return (
    <div
      role="dialog"
      aria-label="AI chat assistant"
      className="fixed bottom-6 right-6 z-40 flex flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
      style={{
        width: 'min(92vw, 400px)',
        height: 'min(75vh, 600px)',
        border: '1px solid var(--line)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 text-white"
        style={{ background: 'var(--teal)' }}
      >
        <div className="flex items-center gap-2">
          <Sparkles size={18} />
          <span className="font-semibold text-sm">Ask about this report</span>
        </div>
        <button
          onClick={() => setOpen(false)}
          aria-label="Close chat"
          className="rounded-md p-1 hover:bg-white/20"
        >
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3" aria-live="polite">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
              Ask me anything about your results. I explain them in plain language, using only
              what is in your reports.
            </p>
            <div className="flex flex-col gap-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={sending}
                  className="text-left text-sm rounded-xl px-3 py-2 transition-colors hover:opacity-80"
                  style={{ background: 'var(--teal-soft)', color: 'var(--ink)' }}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === 'user' ? 'rounded-2xl rounded-br-md' : 'rounded-2xl rounded-bl-md'
              }`}
              style={
                m.role === 'user'
                  ? { background: 'var(--teal)', color: '#fff' }
                  : m.isError
                    ? { background: 'var(--amber-soft)', color: 'var(--ink)' }
                    : { background: 'var(--teal-soft)', color: 'var(--ink)' }
              }
            >
              {m.role === 'assistant' && !m.isError ? cleanText(m.text) : m.text}

              {m.sources && m.sources.length > 0 && (
                <details className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                  <summary className="cursor-pointer select-none">
                    Based on {m.sources.length} excerpt{m.sources.length > 1 ? 's' : ''} from your reports
                  </summary>
                  <ul className="mt-1.5 space-y-1.5">
                    {m.sources.map((s, i) => (
                      <li key={i}>
                        <span className="font-medium">{s.report_name}</span>
                        <br />
                        <span className="opacity-80">{s.snippet}…</span>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start">
            <div
              className="flex items-center gap-2 rounded-2xl rounded-bl-md px-3.5 py-2.5 text-sm"
              style={{ background: 'var(--teal-soft)', color: 'var(--muted)' }}
            >
              <Loader2 size={14} className="animate-spin" />
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-3 py-3 space-y-2" style={{ borderTop: '1px solid var(--line)' }}>
        <label
          className="flex items-center gap-2 text-xs cursor-pointer"
          style={{ color: 'var(--muted)' }}
        >
          <input
            type="checkbox"
            checked={searchAll}
            onChange={(e) => setSearchAll(e.target.checked)}
          />
          Search across all my reports
        </label>

        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            rows={2}
            maxLength={1000}
            placeholder="Ask a question about your results…"
            aria-label="Your question"
            className="flex-1 resize-none rounded-xl px-3 py-2 text-sm outline-none"
            style={{ border: '1px solid var(--line)', color: 'var(--ink)' }}
          />
          <button
            onClick={() => send(input)}
            disabled={sending || !input.trim()}
            aria-label="Send question"
            className="rounded-xl p-2.5 text-white transition-opacity disabled:opacity-40"
            style={{ background: 'var(--teal)' }}
          >
            <Send size={18} />
          </button>
        </div>

        <p className="text-[11px] leading-snug" style={{ color: 'var(--muted)' }}>
          AI-generated explanation, not medical advice. Please talk to your doctor about your results.
        </p>
      </div>
    </div>
  );
}
