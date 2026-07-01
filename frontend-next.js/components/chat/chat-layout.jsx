"use client";

import React, { useState, useCallback } from "react";
import { EmptyState } from "@/components/chat/empty-state";
import { ChatMessages } from "@/components/chat/chat-messages";
import { PromptContainer } from "@/components/chat/prompt-container";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import { Spinner } from "@/components/ui/spinner";

function generateId() {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function ChatLayout({
  activeChatId,
  setActiveChatId,
  messages = [],
  setMessages,
  refreshHistory,
  messagesLoading
}) {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");

  const hasMessages = messages.length > 0;

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || loading) return;

      if (!user) {
        toast.error("Please authenticate to communicate.");
        return;
      }

      const startTime = Date.now();
      const tempId = generateId();
      const optimisticMsg = {
        id: tempId,
        question: text.trim(),
        answer: null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, optimisticMsg]);
      setLoading(true);

      let currentChatId = activeChatId;

      try {
        // 1. POST to BFF /api/chat
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-Frontend-Start-Time": startTime.toString()
          },
          body: JSON.stringify({
            chatid: currentChatId,
            question: text.trim(),
          }),
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || "Failed to get response from assistant");
        }

        const data = await res.json();
        const bffEnd = Date.now();

        // 2. If a new chat session was created dynamically, update the active ID
        if (!currentChatId && data.chatid) {
          setActiveChatId(data.chatid);
        }

        // 3. Save / update state with DB returned QA pair message
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === tempId ? data.message : msg
          )
        );

        // Defer history refresh to avoid delaying current message rendering
        setTimeout(() => {
          refreshHistory();
        }, 500);

        // Performance Timing Summary Logging
        setTimeout(() => {
          const uiRenderedTime = Date.now();
          const totalDuration = uiRenderedTime - startTime;
          const networkTime = bffEnd - startTime;

          console.log("==================================================");
          console.log("          PERFORMANCE TIMING SUMMARY              ");
          console.log("==================================================");
          console.log(`[Frontend] Request Started               : 0 ms`);
          console.log(`[Frontend] Network Roundtrip to BFF      : ${networkTime} ms`);

          if (data.timing) {
            const t = data.timing;
            const cacheHitText = t.cache_hit ? "HIT" : "MISS";
            console.log(`[Cache Status]                           : ${cacheHitText}`);
            console.log(`[FastAPI] Validation Time                : ${(t.validation_time * 1000).toFixed(1)} ms`);
            console.log(`[FastAPI] Conversation Detection         : ${(t.conversation_detection_time * 1000).toFixed(1)} ms`);

            if (!t.cache_hit) {
              console.log(`[FastAPI] Embedding Time                 : ${(t.embedding_time * 1000).toFixed(1)} ms`);
              console.log(`[FastAPI] Retrieval Time                 : ${(t.retrieval_time * 1000).toFixed(1)} ms`);
              console.log(`[FastAPI] Prompt Build Time              : ${(t.prompt_build_time * 1000).toFixed(1)} ms`);
              if (t.gemini_time > 0) {
                console.log(`[FastAPI] Gemini API Call                : ${(t.gemini_time * 1000).toFixed(1)} ms`);
              }
            }
            console.log(`[FastAPI] Total Processing Time          : ${(t.total_time * 1000).toFixed(1)} ms`);
          }

          console.log(`[Frontend] UI Rendered                   : ${totalDuration} ms`);
          console.log("==================================================");
        }, 0);

      } catch (err) {
        console.error("Error sending message:", err);
        toast.error(err.message || "Something went wrong. Please try again.");
        // Rollback optimistic message on error
        setMessages((prev) => prev.filter((msg) => msg.id !== tempId));
      } finally {
        setLoading(false);
      }
    },
    [loading, user, activeChatId, setActiveChatId, setMessages, refreshHistory]
  );

  return (
    <div className="flex flex-col flex-1 h-full min-h-0 relative overflow-hidden">
      {messagesLoading ? (
        <div className="flex flex-col flex-1 items-center justify-center">
          <Spinner className="h-8 w-8 text-muted-foreground" />
          <span className="text-xs text-muted-foreground mt-2 font-mono">Loading conversation...</span>
        </div>
      ) : hasMessages ? (
        <>
          {/* Scrollable message area */}
          <ChatMessages messages={messages} isLoading={loading} />

          {/* Fixed prompt input */}
          <PromptContainer
            input={input}
            setInput={setInput}
            onSubmit={sendMessage}
            isLoading={loading}
            fixed
          />
        </>
      ) : (
        <div className="flex flex-col flex-1 items-center justify-center px-4">
          <EmptyState
            input={input}
            setInput={setInput}
            onSubmit={sendMessage}
            isLoading={loading}
          />
        </div>
      )}
    </div>
  );
}