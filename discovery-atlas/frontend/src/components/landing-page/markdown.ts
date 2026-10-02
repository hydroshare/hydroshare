import markdownit from "markdown-it";
import hljs from "highlight.js";
import DOMPurify from "dompurify";

// Shared markdown-it config; output is sanitized before v-html (see below).
const md = markdownit({
  linkify: true,
  typographer: true,
  breaks: true,
  html: true,
  highlight(str: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value;
      } catch (__) {
        /* no highlighting */
      }
    }
    return "";
  },
});

/** Render markdown to sanitized HTML safe for v-html. */
export function renderMarkdown(raw: string): string {
  return DOMPurify.sanitize(md.render(raw || ""));
}

export function isMarkdownFileName(name: string): boolean {
  return /\.md$/i.test(name || "");
}

/** Swap a trailing `.txt` for `.md`, preserving base casing. */
export function toMarkdownFileName(name: string): string {
  return (name || "").replace(/\.txt$/i, ".md");
}
