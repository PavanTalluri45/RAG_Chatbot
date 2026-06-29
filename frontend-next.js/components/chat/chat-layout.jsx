"use client";

import React, { useState, useCallback } from "react";
import { EmptyState } from "@/components/chat/empty-state";
import { ChatMessages } from "@/components/chat/chat-messages";
import { PromptContainer } from "@/components/chat/prompt-container";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";

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
  refreshHistory
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
        refreshHistory();
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
      {hasMessages ? (
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