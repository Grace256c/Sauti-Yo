import {
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  FormEvent,
  KeyboardEvent,
} from "react";
import { useTranslation } from "react-i18next";
import {
  MessageCircle,
  Send,
  X,
} from "lucide-react";

type Message = {
  id: number;
  role: "user" | "assistant";
  text: string;
};

type ChatResponse = {
  matched: boolean;
  reply?: string;
  message?: string;
  situation?: {
    slug: string;
    title: string;
    risk_level: string;
  } | null;
};

export default function ChatWidget() {
  const { i18n } = useTranslation();

  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [
    activeSituationSlug,
    setActiveSituationSlug,
  ] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      role: "assistant",
      text:
        "Hello! I'm the Sauti Yo Assistant. Tell me what is happening, and I'll help you understand the available rights information and possible next steps.",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement | null>(
    null,
  );

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const sendMessage = async () => {
    const trimmed = input.trim();

    if (!trimmed || loading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now(),
      role: "user",
      text: trimmed,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setInput("");
    setLoading(true);

    try {
      const result = await fetch(
        "http://127.0.0.1:8000/api/chat/",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: trimmed,
            language:
              i18n.resolvedLanguage ||
              i18n.language ||
              "en",
            situation_slug:
              activeSituationSlug,
          }),
        },
      );

      if (!result.ok) {
        throw new Error(
          `Chat request failed: ${result.status}`,
        );
      }

      const data: ChatResponse =
        await result.json();

      const assistantText =
        data.reply ||
        data.message ||
        "I couldn't find an answer for that. Please try describing the situation in another way.";

      if (data.situation?.slug) {
        setActiveSituationSlug(
          data.situation.slug,
        );
      }

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: assistantText,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((current) => [
        ...current,
        {
          id: Date.now() + 1,
          role: "assistant",
          text:
            "I couldn't connect to the Sauti Yo service. Please try again in a moment.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    void sendMessage();
  };

  const handleKeyDown = (
    event: KeyboardEvent<HTMLTextAreaElement>,
  ) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void sendMessage();
    }
  };

  return (
    <>
      {open && (
        <section
          className="
            fixed bottom-24 right-4 z-[70]
            flex h-[72vh] w-[calc(100%-2rem)]
            max-w-md flex-col overflow-hidden
            rounded-2xl border border-border
            bg-surface shadow-2xl
            sm:right-6
          "
          aria-label="Sauti Yo Assistant"
        >
          <header
            className="
              flex items-center justify-between
              border-b border-border
              bg-surface px-5 py-4
            "
          >
            <div className="flex items-center gap-3">
              <div
                className="
                  flex h-10 w-10 items-center
                  justify-center rounded-full
                  bg-gold/15 text-gold-deep
                "
              >
                <MessageCircle className="h-5 w-5" />
              </div>

              <div>
                <h2 className="font-semibold text-text-primary">
                  Sauti Yo Assistant
                </h2>

                <p className="text-xs text-text-secondary">
                  Rights information & next steps
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close chat"
              className="
                flex h-9 w-9 items-center
                justify-center rounded-full
                text-text-secondary transition
                hover:bg-background
                hover:text-text-primary
              "
            >
              <X className="h-5 w-5" />
            </button>
          </header>

          <div
            className="
              flex-1 space-y-4 overflow-y-auto
              bg-background/50 p-4
            "
          >
            {messages.map((message) => (
              <div
                key={message.id}
                className={
                  message.role === "user"
                    ? "flex justify-end"
                    : "flex justify-start"
                }
              >
                <div
                  className={
                    message.role === "user"
                      ? `
                        max-w-[82%] whitespace-pre-wrap
                        rounded-2xl rounded-br-md
                        bg-gold px-4 py-3
                        text-sm leading-6 text-white
                      `
                      : `
                        max-w-[88%] whitespace-pre-wrap
                        rounded-2xl rounded-bl-md
                        border border-border
                        bg-surface px-4 py-3
                        text-sm leading-6
                        text-text-primary shadow-sm
                      `
                  }
                >
                  {message.text}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div
                  className="
                    rounded-2xl rounded-bl-md
                    border border-border
                    bg-surface px-4 py-3
                    text-sm text-text-secondary
                    shadow-sm
                  "
                >
                  <div className="flex gap-1">
                    <span className="animate-bounce">
                      •
                    </span>
                    <span className="animate-bounce [animation-delay:150ms]">
                      •
                    </span>
                    <span className="animate-bounce [animation-delay:300ms]">
                      •
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form
            onSubmit={handleSubmit}
            className="
              border-t border-border
              bg-surface p-4
            "
          >
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(event) =>
                  setInput(event.target.value)
                }
                onKeyDown={handleKeyDown}
                placeholder="Tell me what's happening..."
                rows={1}
                disabled={loading}
                className="
                  max-h-28 min-h-[48px]
                  flex-1 resize-none
                  rounded-xl border border-border
                  bg-background px-4 py-3
                  text-sm text-text-primary
                  outline-none transition
                  placeholder:text-text-secondary
                  focus:border-gold
                  focus:ring-2 focus:ring-gold/20
                  disabled:opacity-60
                "
              />

              <button
                type="submit"
                disabled={
                  loading || !input.trim()
                }
                aria-label="Send message"
                className="
                  flex h-12 w-12 shrink-0
                  items-center justify-center
                  rounded-xl bg-gold
                  text-white transition
                  hover:opacity-90
                  disabled:cursor-not-allowed
                  disabled:opacity-40
                "
              >
                <Send className="h-5 w-5" />
              </button>
            </div>

            <p
              className="
                mt-2 text-center text-[11px]
                text-text-secondary
              "
            >
              Sauti Yo provides rights information,
              not legal representation.
            </p>
          </form>
        </section>
      )}

      <button
        type="button"
        onClick={() =>
          setOpen((current) => !current)
        }
        aria-label={
          open
            ? "Close Sauti Yo Assistant"
            : "Open Sauti Yo Assistant"
        }
        className="
          fixed bottom-6 right-4 z-[70]
          flex h-14 w-14 items-center
          justify-center rounded-full
          bg-gold text-white shadow-xl
          transition
          hover:scale-105
          sm:right-6
        "
      >
        {open ? (
          <X className="h-6 w-6" />
        ) : (
          <MessageCircle className="h-6 w-6" />
        )}
      </button>
    </>
  );
}