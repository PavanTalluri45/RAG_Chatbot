"use client";

import React from "react";
import { PromptBox } from "@/components/ui/prompt-input";

export const PromptContainer = React.memo(function PromptContainer({
  input,
  setInput,
  onSubmit,
  isLoading,
  fixed = true,
}) {
  const textareaRef = React.useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSubmit(input.trim());
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const inner = (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto w-full">
      <PromptBox
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        isLoading={isLoading}
        aria-label="Type your message"
      />
    </form>
  );

  if (!fixed) {
    return <div className="w-full">{inner}</div>;
  }

  return (
    <div className="absolute bottom-0 left-0 right-0 pt-2 pb-4 px-4">
      {inner}
    </div>
  );
});