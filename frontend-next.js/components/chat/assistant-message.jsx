"use client";

import React from "react";
import { Bot } from "lucide-react";
import { Mermaid } from "@/components/chat/mermaid";

// --- Inline minimal markdown renderer ---
function renderMarkdown(text) {
  if (!text) return null;

  const lines = text.split("\n");
  const elements = [];
  let i = 0;
  let keyCounter = 0;

  const key = () => `md-${keyCounter++}`;

  function inlineFormat(str) {
    const parts = [];
    const codeRegex = /`([^`]+)`/g;
    let lastIndex = 0;
    let match;
    const segments = [];

    while ((match = codeRegex.exec(str)) !== null) {
      if (match.index > lastIndex) segments.push({ type: "text", val: str.slice(lastIndex, match.index) });
      segments.push({ type: "code", val: match[1] });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < str.length) segments.push({ type: "text", val: str.slice(lastIndex) });

    return segments.map((seg, idx) => {
      if (seg.type === "code") {
        return (
          <code key={idx} className="px-1.5 py-0.5 rounded bg-muted text-[0.8em] font-mono text-foreground/90">
            {seg.val}
          </code>
        );
      }
      return processTextSegment(seg.val, idx);
    });
  }

  function processTextSegment(str, outerKey) {
    const regex = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(\[([^\]]+)\]\(([^)]+)\))/g;
    const parts = [];
    let last = 0;
    let m;

    while ((m = regex.exec(str)) !== null) {
      if (m.index > last) parts.push(<span key={`${outerKey}-t${last}`}>{str.slice(last, m.index)}</span>);

      if (m[1]) {
        parts.push(<strong key={`${outerKey}-b${m.index}`} className="font-semibold">{m[2]}</strong>);
      } else if (m[3]) {
        parts.push(<em key={`${outerKey}-i${m.index}`}>{m[4]}</em>);
      } else if (m[5]) {
        parts.push(
          <a key={`${outerKey}-a${m.index}`} href={m[7]} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-2 hover:opacity-80">
            {m[6]}
          </a>
        );
      }
      last = m.index + m[0].length;
    }
    if (last < str.length) parts.push(<span key={`${outerKey}-tl`}>{str.slice(last)}</span>);

    return parts.length > 0 ? <span key={outerKey}>{parts}</span> : str;
  }

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      const codeContent = codeLines.join("\n");
      if (lang === "mermaid") {
        elements.push(<Mermaid key={key()} chart={codeContent} />);
      } else {
        elements.push(
          <div key={key()} className="my-3 rounded-lg overflow-hidden border border-border">
            {lang && (
              <div className="px-4 py-1.5 bg-muted/50 text-xs text-muted-foreground font-mono border-b border-border">
                {lang}
              </div>
            )}
            <pre className="overflow-x-auto p-4 bg-muted/30 text-sm font-mono leading-relaxed">
              <code>{codeContent}</code>
            </pre>
          </div>
        );
      }
      i++;
      continue;
    }

    // Headings
    const headingMatch = line.match(/^(#{1,3})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const text = headingMatch[2];
      const classes = [
        "font-semibold mt-4 mb-1.5",
        level === 1 ? "text-xl" : level === 2 ? "text-lg" : "text-base",
      ].join(" ");
      elements.push(
        <p key={key()} className={classes}>
          {inlineFormat(text)}
        </p>
      );
      i++;
      continue;
    }

    // Table
    if (line.includes("|") && lines[i + 1] && lines[i + 1].match(/^\|?[\s\-|:]+\|/)) {
      const tableLines = [];
      while (i < lines.length && lines[i].includes("|")) {
        tableLines.push(lines[i]);
        i++;
      }
      const rows = tableLines.map((r) =>
        r.split("|").filter((_, idx, arr) => idx !== 0 || r.trim().startsWith("|")).map((c) => c.trim()).filter((c, idx, arr) => !(idx === 0 && c === "") && !(idx === arr.length - 1 && c === ""))
      );
      const headerRow = rows[0];
      const bodyRows = rows.slice(2);
      elements.push(
        <div key={key()} className="my-3 overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/40">
              <tr>
                {headerRow.map((h, hi) => (
                  <th key={hi} className="px-4 py-2 text-left font-medium text-foreground border-b border-border">
                    {inlineFormat(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {bodyRows.map((row, ri) => (
                <tr key={ri} className="border-b border-border/50 last:border-0 hover:bg-muted/20">
                  {row.map((cell, ci) => (
                    <td key={ci} className="px-4 py-2 text-muted-foreground">
                      {inlineFormat(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    // Unordered list
    if (/^[\-*]\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^[\-*]\s/.test(lines[i])) {
        listItems.push(lines[i].replace(/^[\-*]\s/, ""));
        i++;
      }
      elements.push(
        <ul key={key()} className="my-2 pl-5 space-y-1 list-disc text-sm text-foreground/90">
          {listItems.map((item, idx) => (
            <li key={idx}>{inlineFormat(item)}</li>
          ))}
        </ul>
      );
      continue;
    }

    // Ordered list
    if (/^\d+\.\s/.test(line)) {
      const listItems = [];
      while (i < lines.length && /^\d+\.\s/.test(lines[i])) {
        listItems.push(lines[i].replace(/^\d+\.\s/, ""));
        i++;
      }
      elements.push(
        <ol key={key()} className="my-2 pl-5 space-y-1 list-decimal text-sm text-foreground/90">
          {listItems.map((item, idx) => (
            <li key={idx}>{inlineFormat(item)}</li>
          ))}
        </ol>
      );
      continue;
    }

    // Blank line
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Paragraph
    elements.push(
      <p key={key()} className="text-sm leading-relaxed text-foreground/90 my-1">
        {inlineFormat(line)}
      </p>
    );
    i++;
  }

  return elements;
}

export const AssistantMessage = React.memo(function AssistantMessage({ content }) {
  const rendered = React.useMemo(() => renderMarkdown(content), [content]);

  return (
    <div className="flex items-start gap-3 py-4 px-2 group">
      <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted flex items-center justify-center select-none mt-0.5">
        <Bot className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="prose-like">{rendered}</div>
      </div>
    </div>
  );
});