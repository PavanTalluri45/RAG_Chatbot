"use client";

import React from "react";
import { UserMessage } from "@/components/chat/user-message";
import { AssistantMessage } from "@/components/chat/assistant-message";

export const Message = React.memo(function Message({ message }) {
  const timestamp = message.created_at
    ? new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "";

  return (
    <React.Fragment>
      <UserMessage content={message.question} timestamp={timestamp} />
      {message.answer && <AssistantMessage content={message.answer} />}
    </React.Fragment>
  );
});