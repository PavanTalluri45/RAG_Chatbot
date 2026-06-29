"use client";

import React from "react";

const SUGGESTIONS = [
  "What is the leave policy?",
  "How do I apply for leave?",
  "What are the office timings?",
  "Explain the work from home policy.",
];

export const SuggestionCards = React.memo(function SuggestionCards({ onSelect }) {
  return (
    <div className="w-full">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => onSelect(suggestion)}
            className="
              group text-left px-4 py-3 rounded-xl
              border border-border bg-transparent
              text-sm text-muted-foreground
              hover:bg-accent hover:text-foreground hover:border-accent
              transition-all duration-150 ease-in-out
              cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
            "
            aria-label={`Ask: ${suggestion}`}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
});