"use client";

import { useState, useRef, useLayoutEffect, useEffect, forwardRef, useImperativeHandle } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

function cn(...inputs) {
  return inputs.filter(Boolean).join(" ");
}

export const PromptBox = forwardRef(({ className, isLoading = false, ...props }, ref) => {
  const internalTextareaRef = useRef(null);
  const [value, setValue] = useState("");

  useImperativeHandle(ref, () => internalTextareaRef.current, []);

  useLayoutEffect(() => {
    const textarea = internalTextareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      const newHeight = Math.min(textarea.scrollHeight, 200);
      textarea.style.height = `${newHeight}px`;
    }
  }, [value]);

  const handleInputChange = (e) => {
    setValue(e.target.value);
    if (props.onChange) props.onChange(e);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      const form = internalTextareaRef.current?.closest("form");
      if (form) {
        form.requestSubmit();
      }
    }
    if (props.onKeyDown) props.onKeyDown(e);
  };

  useEffect(() => {
    if (props.value !== undefined && props.value !== value) {
      setValue(props.value);
    }
  }, [props.value]);

  const hasValue = value.trim().length > 0;

  return (
    <div
      className={cn(
        "flex flex-col rounded-[28px] p-2 shadow-sm transition-colors bg-white border dark:bg-[#303030] dark:border-transparent cursor-text",
        className
      )}
    >
      <textarea
        ref={internalTextareaRef}
        rows={1}
        value={value}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        placeholder="Message..."
        className="w-full resize-none border-0 bg-transparent p-3 text-foreground dark:text-white placeholder:text-muted-foreground dark:placeholder:text-gray-300 focus:ring-0 focus-visible:outline-none min-h-12"
        aria-label="Chat message input"
      />

      <div className="mt-0.5 p-1 pt-0 flex justify-end">
        <Button
          type="submit"
          disabled={!hasValue || isLoading}
          size="icon"
          className="h-8 w-8 rounded-full bg-black text-white hover:bg-black/80 dark:bg-white dark:text-black dark:hover:bg-white/80 disabled:bg-black/40 dark:disabled:bg-[#515151]"
          aria-label="Send message"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <ArrowUp className="h-5 w-5" />
          )}
          <span className="sr-only">Send message</span>
        </Button>
      </div>
    </div>
  );
});