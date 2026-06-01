"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Send, TreePine, Volume2, VolumeX, Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { DEFAULT_STUDENT_ID } from "@/lib/config";
import { getGuidanceContext, generateTTSAudio, sendDifyChat } from "@/lib/api";

const DIFY_CONFIGURED = process.env.NEXT_PUBLIC_DIFY_ENABLED !== "false";

type SpeechRecognitionEventType = {
  resultIndex: number;
  results: SpeechRecognitionResultList;
};

interface SpeechRecognitionInstance extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  onresult: ((e: SpeechRecognitionEventType) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
}

function createSpeechRecognition(): SpeechRecognitionInstance | null {
  if (typeof window === "undefined") return null;
  const Ctor =
    (window as unknown as Record<string, unknown>).SpeechRecognition ??
    (window as unknown as Record<string, unknown>).webkitSpeechRecognition;
  if (!Ctor) return null;
  return new (Ctor as new () => SpeechRecognitionInstance)();
}

interface ChatMessage {
  id: string;
  role: "user" | "bot";
  content: string;
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function classifyError(err: unknown): string {
  if (!(err instanceof Error)) return "发送失败，请重试";
  const msg = err.message;
  if (/Failed to fetch|NetworkError|fetch failed|network/i.test(msg)) {
    return "树精灵暂时离线，请稍后再试 🌿";
  }
  if (/\b40[13]\b/.test(msg)) {
    return "服务认证失败，请联系老师";
  }
  if (/\b500\b/.test(msg)) {
    return "树精灵思考中出了点问题，请重试";
  }
  return "发送失败，请重试";
}

// ---------------------------------------------------------------------------
// TTS: LaTeX / Markdown → clean Chinese text
// ---------------------------------------------------------------------------

function cleanTextForTTS(raw: string): string {
  let t = raw;

  // \frac{a}{b} → a分之b  (handles nested braces via greedy inner match)
  t = t.replace(/\\frac\{([^}]*)\}\{([^}]*)\}/g, "$1分之$2");

  // LaTeX operator commands
  t = t.replace(/\\times/g, "乘以");
  t = t.replace(/\\div/g, "除以");
  t = t.replace(/\\pm/g, "加减");
  t = t.replace(/\\neq/g, "不等于");
  t = t.replace(/\\leq/g, "小于等于");
  t = t.replace(/\\geq/g, "大于等于");
  t = t.replace(/\\approx/g, "约等于");
  t = t.replace(/\\cdot/g, "乘");

  // LaTeX delimiters
  t = t.replace(/\\\(|\\\)/g, "");
  t = t.replace(/\\\[|\\\]/g, "");

  // Markdown bold / italic
  t = t.replace(/\*\*(.+?)\*\*/g, "$1");
  t = t.replace(/\*(.+?)\*/g, "$1");

  // Markdown headers
  t = t.replace(/^#{1,6}\s+/gm, "");

  // Horizontal rules
  t = t.replace(/---+/g, "");

  // Remaining backslash commands (e.g. \text{...})
  t = t.replace(/\\text\{([^}]*)\}/g, "$1");
  t = t.replace(/\\[a-zA-Z]+/g, "");

  // Strip stray braces / brackets used by LaTeX
  t = t.replace(/[{}]/g, "");

  // Collapse whitespace
  t = t.replace(/\s+/g, " ").trim();

  return t;
}

// ---------------------------------------------------------------------------
// TTS — Edge-TTS backend with Web Speech API fallback
// ---------------------------------------------------------------------------

async function playBackendTTS(text: string): Promise<HTMLAudioElement> {
  const blob = await generateTTSAudio(text);
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.onended = () => URL.revokeObjectURL(url);
  audio.onerror = () => URL.revokeObjectURL(url);
  return audio;
}

function speakWithWebAPI(cleaned: string): void {
  const utterance = new SpeechSynthesisUtterance(cleaned);
  utterance.lang = "zh-CN";
  utterance.rate = 0.9;
  const voices = window.speechSynthesis.getVoices();
  const zhVoice = voices.find(
    (v) => v.lang === "zh-CN" || v.lang === "zh" || v.lang.startsWith("zh-"),
  );
  if (zhVoice) utterance.voice = zhVoice;
  window.speechSynthesis.speak(utterance);
}

function useTTS() {
  const speakingIdRef = useRef<string | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentUrlRef = useRef<string | null>(null);
  const [speakingId, setSpeakingId] = useState<string | null>(null);

  const webSpeechSupported =
    typeof window !== "undefined" && typeof window.speechSynthesis !== "undefined";

  const supported = true;

  const revokeCurrentUrl = useCallback(() => {
    if (currentUrlRef.current) {
      URL.revokeObjectURL(currentUrlRef.current);
      currentUrlRef.current = null;
    }
  }, []);

  const speak = useCallback(
    (text: string, messageId: string) => {
      if (speakingIdRef.current === messageId) {
        if (currentAudioRef.current) {
          currentAudioRef.current.pause();
          currentAudioRef.current = null;
        }
        revokeCurrentUrl();
        window.speechSynthesis?.cancel();
        speakingIdRef.current = null;
        setSpeakingId(null);
        return;
      }

      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      revokeCurrentUrl();
      window.speechSynthesis?.cancel();

      const cleaned = cleanTextForTTS(text);
      if (!cleaned) return;

      speakingIdRef.current = messageId;
      setSpeakingId(messageId);

      const onDone = () => {
        speakingIdRef.current = null;
        setSpeakingId(null);
        currentAudioRef.current = null;
        revokeCurrentUrl();
      };

      const fallbackToWebSpeech = () => {
        revokeCurrentUrl();
        if (webSpeechSupported) {
          speakWithWebAPI(cleaned);
          setTimeout(onDone, Math.max(cleaned.length * 150, 2000));
        } else {
          onDone();
        }
      };

      playBackendTTS(cleaned)
        .then((audio) => {
          currentAudioRef.current = audio;
          currentUrlRef.current = audio.src;
          audio.onended = () => {
            URL.revokeObjectURL(audio.src);
            currentUrlRef.current = null;
            onDone();
          };
          audio.onerror = () => {
            URL.revokeObjectURL(audio.src);
            currentUrlRef.current = null;
            fallbackToWebSpeech();
          };
          audio.play().catch(() => {
            URL.revokeObjectURL(audio.src);
            currentUrlRef.current = null;
            fallbackToWebSpeech();
          });
        })
        .catch(fallbackToWebSpeech);
    },
    [webSpeechSupported, revokeCurrentUrl],
  );

  const stop = useCallback(() => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    revokeCurrentUrl();
    if (webSpeechSupported) {
      window.speechSynthesis.cancel();
    }
    speakingIdRef.current = null;
    setSpeakingId(null);
  }, [webSpeechSupported, revokeCurrentUrl]);

  return { supported, speakingId, speak, stop };
}

function useSpeechInput(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const recogRef = useRef<SpeechRecognitionInstance | null>(null);

  const supported = typeof window !== "undefined" && !!createSpeechRecognition();

  const start = useCallback(() => {
    const recog = createSpeechRecognition();
    if (!recog) return;
    recog.lang = "zh-CN";
    recog.interimResults = true;
    recog.continuous = false;

    recog.onresult = (e: SpeechRecognitionEventType) => {
      let transcript = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        transcript += e.results[i][0].transcript;
      }
      if (transcript) onResult(transcript);
    };

    recog.onerror = () => {
      setListening(false);
      recogRef.current = null;
    };

    recog.onend = () => {
      setListening(false);
      recogRef.current = null;
    };

    recogRef.current = recog;
    setListening(true);
    recog.start();
  }, [onResult]);

  const stop = useCallback(() => {
    if (recogRef.current) {
      recogRef.current.stop();
      recogRef.current = null;
    }
    setListening(false);
  }, []);

  const toggle = useCallback(() => {
    if (listening) {
      stop();
    } else {
      start();
    }
  }, [listening, start, stop]);

  useEffect(() => {
    return () => {
      if (recogRef.current) recogRef.current.abort();
    };
  }, []);

  return { supported, listening, toggle, stop };
}

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-forest-100">
        <TreePine className="h-4 w-4 text-forest-600" />
      </div>
      <div className="max-w-[75%] rounded-2xl rounded-bl-sm bg-forest-100 px-4 py-3">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-forest-400 [animation-delay:0ms]" />
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-forest-400 [animation-delay:150ms]" />
          <span className="inline-block h-2 w-2 animate-bounce rounded-full bg-forest-400 [animation-delay:300ms]" />
        </span>
      </div>
    </div>
  );
}

interface GuidanceChatProps {
  /** Student id forwarded to Dify as the `user` field. */
  studentId?: string;
  /** Optional welcome message shown before the user sends anything. */
  welcomeMessage?: string;
  className?: string;
}

export function GuidanceChat({
  studentId = "demo-student",
  welcomeMessage,
  className,
}: GuidanceChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [autoRead, setAutoRead] = useState(false);
  const [studentContext, setStudentContext] = useState("");

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesLengthRef = useRef(0);

  useEffect(() => {
    const effectiveId = studentId || DEFAULT_STUDENT_ID;
    getGuidanceContext(effectiveId).then((ctx) => {
      if (ctx) setStudentContext(ctx);
    });
  }, [studentId]);

  const tts = useTTS();

  const handleSpeechResult = useCallback((text: string) => {
    setInput((prev) => {
      const sep = prev.trim() ? " " : "";
      return prev + sep + text;
    });
  }, []);

  const stt = useSpeechInput(handleSpeechResult);

  // Ensure voices are loaded (some browsers load them asynchronously)
  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;
    window.speechSynthesis.getVoices();
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }, []);

  useEffect(() => {
    if (welcomeMessage && messages.length === 0) {
      setMessages([
        { id: generateId(), role: "bot", content: welcomeMessage },
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-read new bot messages
  useEffect(() => {
    if (!autoRead || messages.length <= messagesLengthRef.current) {
      messagesLengthRef.current = messages.length;
      return;
    }
    messagesLengthRef.current = messages.length;
    const last = messages[messages.length - 1];
    if (last && last.role === "bot" && tts.supported) {
      tts.speak(last.content, last.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages, autoRead]);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  useEffect(() => {
    if (!DIFY_CONFIGURED && messages.length === 0) {
      setMessages([
        { id: generateId(), role: "bot", content: "树精灵服务尚未配置，请联系老师" },
      ]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    setError(null);

    const userMsg: ChatMessage = {
      id: generateId(),
      role: "user",
      content: trimmed,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const historyForApi = messages.map((m) => ({
        role: m.role === "bot" ? "bot" as const : "user" as const,
        content: m.content,
      }));

      const data = await sendDifyChat({
        inputs: !conversationId && studentContext ? { student_context: studentContext } : {},
        query: trimmed,
        user: `student-${studentId}`,
        conversation_id: conversationId || "",
        history: historyForApi,
      });

      const botMsg: ChatMessage = {
        id: generateId(),
        role: "bot",
        content: data.answer,
      };
      setMessages((prev) => [...prev, botMsg]);
      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }
    } catch (err) {
      const message = classifyError(err);
      setError(message);

      setMessages((prev) => [
        ...prev,
        {
          id: generateId(),
          role: "bot",
          content: message,
        },
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [input, loading, conversationId, studentId, studentContext]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div
      className={cn(
        "flex h-full flex-col overflow-hidden rounded-xl border border-forest-200 bg-white shadow-sm",
        className,
      )}
    >
      <div className="flex items-center justify-between border-b border-forest-100 bg-forest-50/50 px-4 py-1.5">
        <span className="text-xs text-forest-600">📢 自动朗读</span>
        {tts.supported ? (
          <button
            type="button"
            onClick={() => {
              if (autoRead) tts.stop();
              setAutoRead((v) => !v);
            }}
            className={cn(
              "relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors",
              autoRead ? "bg-forest-500" : "bg-forest-200",
            )}
            role="switch"
            aria-checked={autoRead}
            aria-label="自动朗读开关"
          >
            <span
              className={cn(
                "inline-block h-3.5 w-3.5 rounded-full bg-white shadow-sm transition-transform",
                autoRead ? "translate-x-4.5" : "translate-x-0.5",
              )}
            />
          </button>
        ) : (
          <span className="text-[10px] text-forest-400">浏览器不支持语音</span>
        )}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-4 py-6"
        style={{
          background:
            "linear-gradient(180deg, var(--color-forest-50) 0%, #fff 40%)",
        }}
      >
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={cn(
                "flex items-end gap-2",
                msg.role === "user" && "flex-row-reverse",
              )}
            >
              {msg.role === "bot" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-forest-100">
                  <TreePine className="h-4 w-4 text-forest-600" />
                </div>
              )}
              {msg.role === "user" && (
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warm-100">
                  <span className="text-sm">🧒</span>
                </div>
              )}

              <div
                className={cn(
                  "max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                  msg.role === "bot" &&
                    "rounded-bl-sm bg-forest-100 text-forest-900",
                  msg.role === "user" &&
                    "rounded-br-sm bg-warm-100 text-warm-900",
                )}
              >
                <span>{msg.content}</span>

                {msg.role === "bot" && tts.supported && (
                  <button
                    type="button"
                    onClick={() => tts.speak(msg.content, msg.id)}
                    className={cn(
                      "mt-1.5 ml-auto flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[11px] transition-colors",
                      tts.speakingId === msg.id
                        ? "bg-warm-200/60 text-warm-600 animate-pulse"
                        : "text-forest-500 hover:bg-forest-200/60 hover:text-forest-700",
                    )}
                    aria-label={
                      tts.speakingId === msg.id ? "停止朗读" : "朗读"
                    }
                  >
                    {tts.speakingId === msg.id ? (
                      <VolumeX className="h-3 w-3" />
                    ) : (
                      <Volume2 className="h-3 w-3" />
                    )}
                    {tts.speakingId === msg.id ? "停止" : "朗读"}
                  </button>
                )}
              </div>
            </div>
          ))}

          {loading && <TypingIndicator />}
        </div>
      </div>

      {error && (
        <div className="border-t border-volcano-200 bg-volcano-50 px-4 py-2 text-xs text-volcano-500">
          ⚠️ 连接出现问题：{error}
        </div>
      )}

      <div className="border-t border-forest-100 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-2xl items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={stt.listening ? "正在听你说话..." : "输入计算题或问题..."}
            aria-label="输入计算题或问题"
            disabled={loading || !DIFY_CONFIGURED}
            className={cn(
              "h-10 flex-1 rounded-xl border bg-forest-50/40 px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 disabled:opacity-50",
              stt.listening
                ? "border-forest-400 ring-2 ring-forest-300 animate-pulse"
                : "border-forest-200 focus:border-forest-400 focus:ring-forest-200",
            )}
          />
          {stt.supported && (
            <Button
              size="icon-lg"
              variant="outline"
              onClick={stt.toggle}
              disabled={loading || !DIFY_CONFIGURED}
              className={cn(
                "rounded-xl transition-colors",
                stt.listening
                  ? "bg-forest-500 text-white border-forest-500 hover:bg-forest-600 hover:border-forest-600 animate-pulse"
                  : "border-forest-200 text-forest-500 hover:bg-forest-50 hover:text-forest-700",
              )}
              aria-label={stt.listening ? "停止语音输入" : "语音输入"}
            >
              {stt.listening ? (
                <MicOff className="h-4 w-4" />
              ) : (
                <Mic className="h-4 w-4" />
              )}
            </Button>
          )}
          <Button
            size="icon-lg"
            onClick={sendMessage}
            disabled={loading || !input.trim() || !DIFY_CONFIGURED}
            className="rounded-xl bg-forest-500 text-white hover:bg-forest-600 disabled:opacity-40"
            aria-label="发送消息"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
