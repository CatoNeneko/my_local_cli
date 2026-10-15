(() => {
  "use strict";

  function safeHttpURL(value) {
    const candidate = String(value || "").trim();
    if (!/^https?:\/\//i.test(candidate)) return null;
    try {
      const parsed = new URL(candidate);
      return parsed.protocol === "http:" || parsed.protocol === "https:" ? parsed.href : null;
    } catch (_error) {
      return null;
    }
  }

  function appendText(parent, value) {
    if (value) parent.append(document.createTextNode(value));
  }

  function nextInlineToken(text, offset) {
    const rest = text.slice(offset);
    const candidates = [];
    const add = (match, type, value, url) => {
      if (match) candidates.push({ index: match.index, match: match[0], type, value, url });
    };

    add(/!\[[^\]\n]*\]\([^\)\n]*\)/.exec(rest), "literal");
    const code = /`([^`\n]+)`/.exec(rest);
    add(code, "code", code && code[1]);
    const strong = /\*\*([^\n]+?)\*\*|__([^\n]+?)__/.exec(rest);
    add(strong, "strong", strong && (strong[1] || strong[2]));
    const markdownLink = /\[([^\]\n]+)\]\(([^)\s]+)\)/.exec(rest);
    if (markdownLink && safeHttpURL(markdownLink[2])) {
      add(markdownLink, "link", markdownLink[1], markdownLink[2]);
    }

    const bareURL = /https?:\/\/[^\s<>"'`]+/i.exec(rest);
    if (bareURL) {
      let url = bareURL[0];
      while (/[.,!?;:]$/.test(url)) url = url.slice(0, -1);
      while (url.endsWith(")") && (url.match(/\)/g) || []).length > (url.match(/\(/g) || []).length) {
        url = url.slice(0, -1);
      }
      if (url && safeHttpURL(url)) {
        candidates.push({ index: bareURL.index, match: url, type: "link", value: url, url });
      }
    }

    candidates.sort((left, right) => left.index - right.index || right.match.length - left.match.length);
    return candidates[0] || null;
  }

  function appendInline(parent, source) {
    const text = String(source || "");
    let offset = 0;
    while (offset < text.length) {
      const token = nextInlineToken(text, offset);
      if (!token) {
        appendText(parent, text.slice(offset));
        break;
      }
      appendText(parent, text.slice(offset, offset + token.index));
      if (token.type === "literal") {
        appendText(parent, token.match);
      } else if (token.type === "code") {
        const code = document.createElement("code");
        code.className = "markdown-inline-code";
        code.textContent = token.value;
        parent.append(code);
      } else if (token.type === "strong") {
        const strong = document.createElement("strong");
        appendInline(strong, token.value);
        parent.append(strong);
      } else if (token.type === "link") {
        const href = safeHttpURL(token.url);
        if (href) {
          const link = document.createElement("a");
          link.textContent = token.value;
          link.href = href;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          parent.append(link);
        } else {
          appendText(parent, token.match);
        }
      }
      offset += token.index + token.match.length;
    }
  }

  function fenceOpening(line) {
    const match = line.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
    if (!match || (match[1][0] === "`" && match[2].includes("`"))) return null;
    return { marker: match[1][0], length: match[1].length, info: match[2].trim() };
  }

  function isFenceClosing(line, fence) {
    const match = line.match(/^ {0,3}(`+|~+)\s*$/);
    return Boolean(match && match[1][0] === fence.marker && match[1].length >= fence.length);
  }

  function appendFence(parent, fence, codeText) {
    const wrapper = document.createElement("div");
    wrapper.className = "markdown-code-block";
    const toolbar = document.createElement("div");
    toolbar.className = "markdown-code-toolbar";
    const language = fence.info.split(/\s+/, 1)[0] || "代码";
    const label = document.createElement("span");
    label.className = "markdown-code-language";
    label.textContent = language;
    const copy = document.createElement("button");
    copy.className = "markdown-copy-button";
    copy.type = "button";
    copy.textContent = "复制代码";
    copy.setAttribute("aria-label", "复制代码块内容");
    const pre = document.createElement("pre");
    const code = document.createElement("code");
    code.textContent = codeText;
    copy.addEventListener("click", async () => {
      try {
        const clipboard = window.navigator.clipboard;
        if (!clipboard || typeof clipboard.writeText !== "function") throw new Error("剪贴板不可用");
        await clipboard.writeText(code.textContent || "");
        copy.textContent = "已复制";
      } catch (_error) {
        copy.textContent = "复制失败";
      }
      window.setTimeout(() => {
        if (copy.isConnected) copy.textContent = "复制代码";
      }, 1600);
    });
    pre.append(code);
    toolbar.append(label, copy);
    wrapper.append(toolbar, pre);
    parent.append(wrapper);
  }

  function listMarker(line) {
    const unordered = line.match(/^ {0,3}[-*+]\s+(.+)$/);
    if (unordered) return { type: "ul", content: unordered[1] };
    const ordered = line.match(/^ {0,3}\d+[.)]\s+(.+)$/);
    return ordered ? { type: "ol", content: ordered[1] } : null;
  }

  function headingMatch(line) {
    return line.match(/^ {0,3}(#{1,6})(?:[ \t]+|$)(.*)$/);
  }

  function isBlockStart(line) {
    return Boolean(fenceOpening(line) || headingMatch(line) || listMarker(line));
  }

  function render(text) {
    const fragment = document.createDocumentFragment();
    const lines = String(text === undefined || text === null ? "" : text).replace(/\r\n?/g, "\n").split("\n");
    let index = 0;

    while (index < lines.length) {
      if (!lines[index].trim()) {
        index += 1;
        continue;
      }

      const fence = fenceOpening(lines[index]);
      if (fence) {
        index += 1;
        const codeLines = [];
        while (index < lines.length && !isFenceClosing(lines[index], fence)) {
          codeLines.push(lines[index]);
          index += 1;
        }
        if (index < lines.length && isFenceClosing(lines[index], fence)) index += 1;
        appendFence(fragment, fence, codeLines.join("\n"));
        continue;
      }

      const heading = headingMatch(lines[index]);
      if (heading) {
        const element = document.createElement("h" + heading[1].length);
        const content = heading[2].replace(/[ \t]+#+[ \t]*$/, "");
        appendInline(element, content);
        fragment.append(element);
        index += 1;
        continue;
      }

      const marker = listMarker(lines[index]);
      if (marker) {
        const list = document.createElement(marker.type);
        while (index < lines.length) {
          const itemMarker = listMarker(lines[index]);
          if (!itemMarker || itemMarker.type !== marker.type) break;
          const item = document.createElement("li");
          appendInline(item, itemMarker.content);
          list.append(item);
          index += 1;
        }
        fragment.append(list);
        continue;
      }

      const paragraphLines = [];
      while (index < lines.length && lines[index].trim() && !isBlockStart(lines[index])) {
        paragraphLines.push(lines[index].trim());
        index += 1;
      }
      if (paragraphLines.length) {
        const paragraph = document.createElement("p");
        appendInline(paragraph, paragraphLines.join(" "));
        fragment.append(paragraph);
      }
    }
    return fragment;
  }

  window.HarnessMarkdown = Object.freeze({ render });
})();
