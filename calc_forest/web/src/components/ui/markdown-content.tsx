"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

interface MarkdownContentProps {
  /** Markdown string (may contain LaTeX math delimiters) */
  content: string;
  /** Extra CSS class on the wrapper */
  className?: string;
}

/**
 * Renders markdown + LaTeX math in a styled container.
 *
 * Supports:
 * - GFM (tables, strikethrough, task lists)
 * - Inline math: `$...$` or `\(...\)`
 * - Block math: `$$...$$` or `\[...\]`
 */
export function MarkdownContent({ content, className = "" }: MarkdownContentProps) {
  return (
    <div className={`prose-math ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p: ({ children }) => (
            <p className="text-[13px] leading-relaxed text-[var(--tone-ink)] mb-2 last:mb-0">
              {children}
            </p>
          ),
          h1: ({ children }) => (
            <h1 className="text-lg font-bold text-[var(--tone-ink)] mt-3 mb-2 first:mt-0">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-bold text-[var(--tone-ink)] mt-3 mb-2 first:mt-0">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-sm font-semibold text-[var(--tone-ink)] mt-2 mb-1 first:mt-0">{children}</h3>
          ),
          strong: ({ children }) => (
            <strong className="font-semibold text-[var(--tone-ink)]">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic text-[var(--tone-ink)]">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="text-[13px] leading-relaxed text-[var(--tone-ink)] list-disc pl-4 mb-2 space-y-0.5">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="text-[13px] leading-relaxed text-[var(--tone-ink)] list-decimal pl-4 mb-2 space-y-0.5">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-[13px] leading-relaxed text-[var(--tone-ink)]">{children}</li>
          ),
          code: ({ children, className: codeClassName }) => {
            const isInline = !codeClassName;
            if (isInline) {
              return (
                <code className="rounded bg-[var(--tone-line)] px-1 py-0.5 text-[12px] font-mono text-[var(--tone-ink)]">
                  {children}
                </code>
              );
            }
            return (
              <code className={`${codeClassName ?? ""} block rounded-lg bg-[var(--tone-line)] p-3 text-[12px] font-mono overflow-x-auto`}>
                {children}
              </code>
            );
          },
          blockquote: ({ children }) => (
            <blockquote className="border-l-3 border-[var(--tone-line)] pl-3 my-2 text-[13px] text-[var(--tone-ink)] opacity-80">
              {children}
            </blockquote>
          ),
          hr: () => (
            <hr className="border-t border-[var(--tone-line)] my-3" />
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className="text-[13px] w-full border-collapse">{children}</table>
            </div>
          ),
          th: ({ children }) => (
            <th className="border border-[var(--tone-line)] px-2 py-1 text-left font-semibold bg-[var(--tone-line)] text-[var(--tone-ink)]">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="border border-[var(--tone-line)] px-2 py-1 text-[var(--tone-ink)]">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
