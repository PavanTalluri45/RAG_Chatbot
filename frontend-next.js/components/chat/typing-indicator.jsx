"use client";

import React from "react";
import { Bot } from "lucide-react";

export const TypingIndicator = React.memo(function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 py-4 px-2" aria-label="Assistant is typing" aria-live="polite">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted flex items-center justify-center select-none">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex items-center gap-1 pt-2">
        <span
          className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce"
          style={{ animationDelay: "0ms", animationDuration: "900ms" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce"
          style={{ animationDelay: "180ms", animationDuration: "900ms" }}
        />
        <span
          className="w-2 h-2 rounded-full bg-muted-foreground/60 animate-bounce"
          style={{ animationDelay: "360ms", animationDuration: "900ms" }}
        />
      </div>
    </div>
  );
});