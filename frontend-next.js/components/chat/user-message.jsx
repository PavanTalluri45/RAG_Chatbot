"use client";

import React from "react";

export const UserMessage = React.memo(function UserMessage({ content, timestamp }) {
  return (
    <div className="flex justify-end py-1">
      <div className="flex flex-col items-end gap-1 max-w-[75%]">
        <div
          className="
            px-4 py-2.5 rounded-[20px] rounded-br-md
            bg-primary text-primary-foreground
            text-sm leading-relaxed
            break-words whitespace-pre-wrap
          "
        >
          {content}
        </div>
        {timestamp && (
          <span className="text-[11px] text-muted-foreground/60 pr-1">
            {timestamp}
          </span>
        )}
      </div>
    </div>
  );
});