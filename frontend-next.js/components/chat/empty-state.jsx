"use client";

import React from "react";
import { SuggestionCards } from "@/components/chat/suggestion-cards";
import { PromptContainer } from "@/components/chat/prompt-container";

export const EmptyState = React.memo(function EmptyState({
  input,
  setInput,
  onSubmit,
  isLoading,
}) {
  return (
    <div className="flex flex-col items-center w-full max-w-2xl gap-5">
      {/* Heading */}
      <div className="text-center">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground mb-1.5">
          How can I help you today?
        </h1>
        <p className="text-sm text-muted-foreground">
          Ask anything about the Employee Handbook.
        </p>
      </div>

      {/* Suggestion cards */}
      <SuggestionCards onSelect={setInput} />

      {/* Prompt input — inline, not fixed */}
      <PromptContainer
        input={input}
        setInput={setInput}
        onSubmit={onSubmit}
        isLoading={isLoading}
        fixed={false}
      />
    </div>
  );
});