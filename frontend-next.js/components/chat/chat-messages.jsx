"use client";

import React, { useEffect, useRef } from "react";
import { Message } from "@/components/chat/message";
import { TypingIndicator } from "@/components/chat/typing-indicator";

export const ChatMessages = React.memo(function ChatMessages({ messages, isLoading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="absolute inset-0 overflow-y-auto px-4 py-4 pb-36" aria-label="Chat messages" role="log" aria-live="polite">
      <div className="max-w-2xl mx-auto w-full space-y-1">
        {messages.map((message) => (
          <Message key={message.id} message={message} />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={bottomRef} aria-hidden="true" />
      </div>
    </div>
  );
});