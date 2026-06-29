"use client";

import React, { useEffect, useRef, useState } from "react";

export function Mermaid({ chart }) {
  const containerRef = useRef(null);
  const [svg, setSvg] = useState("");
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function renderChart() {
      if (!chart) return;
      try {
        const mermaid = (await import("mermaid")).default;
        
        // Initialize mermaid with secure and clean settings
        mermaid.initialize({
          startOnLoad: false,
          theme: "default",
          securityLevel: "loose",
          fontFamily: "var(--font-sans), sans-serif",
          themeVariables: {
            background: "transparent",
            primaryColor: "var(--primary)",
            primaryTextColor: "var(--primary-foreground)",
            lineColor: "var(--border)"
          }
        });

        const uniqueId = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        
        // Render the chart to SVG
        const { svg: renderedSvg } = await mermaid.render(uniqueId, chart);

        if (isMounted) {
          setSvg(renderedSvg);
          setError(null);
        }
      } catch (err) {
        console.error("Mermaid rendering failed:", err);
        if (isMounted) {
          setError(err);
        }
      }
    }

    renderChart();

    return () => {
      isMounted = false;
    };
  }, [chart]);

  if (error) {
    return (
      <div className="my-3 rounded-lg overflow-hidden border border-destructive/20 bg-destructive/5">
        <div className="px-4 py-1.5 bg-destructive/10 text-xs text-destructive font-mono border-b border-destructive/20">
          Mermaid Render Error
        </div>
        <pre className="overflow-x-auto p-4 text-xs font-mono text-destructive leading-relaxed">
          <code>{chart}</code>
        </pre>
      </div>
    );
  }

  if (!svg) {
    return (
      <div className="flex items-center justify-center p-8 text-xs text-muted-foreground animate-pulse font-mono border border-dashed border-border rounded-lg my-3">
        Rendering diagram...
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className="mermaid-diagram my-3 flex justify-center p-4 bg-muted/10 rounded-lg border border-border overflow-x-auto"
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
