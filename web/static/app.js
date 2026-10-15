(() => {
  "use strict";

  const state = {
    sessions: [],
    currentSessionId: null,
    messages: [],
    activeTab: "files",
    memories: [],
    editingMemoryId: null,
    files: [],
    selectedFile: null,
    fileRequestVersion: 0,
    searchResults: null,
    indexSummary: null,
    searchQuery: "",
    searchRequestVersion: 0,
    runs: new Map(),
    runOrder: [],
    diagnosticsRequestVersions: new Map(),
    tasks: [],
    taskSessionId: null,
    taskLoading: false,
    taskError: "",
    taskRequestVersion: 0,
    taskPollTimer: null,
    taskOutputStores: new Map(),
    taskInputDrafts: new Map(),
    gitPreviewRequestVersion: 0,
    git: { sessionId: null, status: null, diff: null, snapshots: [], loading: false, errors: [], snapshotBusy: false },
    gitPreview: null,
    busy: false,
    viewVersion: 0
  };

  const el = (id) => document.getElementById(id);
  const sessionList = el("sessionList");
  const conversation = el("conversation");
  const emptyState = el("emptyState");
  const contextContent = el("contextContent");
  const messageInput = el("messageInput");
  const sendButton = el("sendButton");
  const chatForm = el("chatForm");
  const sessionSearchInput = el("sessionSearchInput");
  const errorBanner = el("errorBanner");
  const apiStatusText = el("apiStatusText");
  const apiStatusDot = el("apiStatusDot");
  const streamStatus = el("streamStatus");

  function node(tag, className, text) {
    const item = document.createElement(tag);
    if (className) item.className = className;
    if (text !== undefined && text !== null) item.textContent = String(text);
    return item;
  }

  function safeJSON(value) {
    if (typeof value === "string") return value;
    try {
      return JSON.stringify(value, null, 2);
    } catch (_error) {
      return String(value);
    }
  }

  function apiPath(path) {
    return path.split("/").map((part, index) => index === 0 ? part : encodeURIComponent(part)).join("/");
  }

  async function api(path, options = {}) {
    const request = {
      method: options.method || "GET",
      headers: { Accept: "application/json" },
      credentials: "same-origin"
    };
    if (options.body !== undefined) {
      request.headers["Content-Type"] = "application/json";
      request.body = JSON.stringify(options.body);
    }
    const response = await fetch(path, request);
    const raw = await response.text();
    let data = null;
    if (raw) {
      try {
        data = JSON.parse(raw);
      } catch (_error) {
        data = raw;
      }
    }
    if (!response.ok) {
      const reason = data && typeof data === "object" && (data.detail || data.error || data.message);
      throw new Error(reason ? String(reason) : "请求失败（HTTP " + response.status + "）");
    }
    setAPIStatus("服务已连接", "online");
    return data;
  }

  function setAPIStatus(label, mode) {
    apiStatusText.textContent = label;
    apiStatusDot.className = "status-dot " + (mode || "");
  }

  function setStreamStatus(label, mode) {
    streamStatus.className = "stream-indicator " + (mode || "");
    streamStatus.lastElementChild.textContent = label;
  }

  function reportError(message) {
    if (!message) {
      errorBanner.hidden = true;
      errorBanner.textContent = "";
      return;
    }
    errorBanner.textContent = message;
    errorBanner.hidden = false;
  }

  function notify(message) {
    const toast = el("toast");
    toast.textContent = message;
    toast.hidden = false;
    window.clearTimeout(notify.timer);
    notify.timer = window.setTimeout(() => { toast.hidden = true; }, 3200);
  }

  function currentSession() {
    return state.sessions.find((session) => session.id === state.currentSessionId) || null;
  }

  function storedSessionId() {
    try {
      return window.localStorage.getItem("ai-workbench.last-session");
    } catch (_error) {
      return null;
    }
  }

  function rememberSession(id) {
    try {
      if (id) window.localStorage.setItem("ai-workbench.last-session", id);
    } catch (_error) {
      // 浏览器禁用本地存储时仍可正常使用本次页面会话。
    }
  }

  function sessionDraftKey(id) {
    return "ai-workbench.draft." + encodeURIComponent(String(id || ""));
  }

  function saveSessionDraft(id, value) {
    if (!id) return;
    try {
      const key = sessionDraftKey(id);
      if (value) window.sessionStorage.setItem(key, String(value));
      else window.sessionStorage.removeItem(key);
    } catch (_error) {
      // 浏览器禁用会话存储时仍可在当前页面中编辑。
    }
  }

  function readSessionDraft(id) {
    if (!id) return "";
    try {
      return window.sessionStorage.getItem(sessionDraftKey(id)) || "";
    } catch (_error) {
      return "";
    }
  }

  function sessionURL(id, suffix) {
    return "/api/sessions/" + encodeURIComponent(id) + (suffix || "");
  }

  function taskURL(sessionId, taskId, suffix) {
    return sessionURL(sessionId, "/tasks/" + encodeURIComponent(taskId) + (suffix || ""));
  }

  const TASK_OUTPUT_CHUNK_BYTES = 16 * 1024;
  const TASK_OUTPUT_TOTAL_BYTES = 64 * 1024;
  const TASK_POLL_INTERVAL_MS = 2000;

  function utf8Length(value) {
    const text = String(value || "");
    if (typeof TextEncoder !== "undefined") return new TextEncoder().encode(text).length;
    return unescape(encodeURIComponent(text)).length;
  }

  function truncateUtf8(value, maxBytes) {
    const text = String(value || "");
    if (maxBytes <= 0) return "";
    if (utf8Length(text) <= maxBytes) return text;
    let output = "";
    let size = 0;
    for (const character of text) {
      const characterBytes = utf8Length(character);
      if (size + characterBytes > maxBytes) break;
      output += character;
      size += characterBytes;
    }
    return output;
  }

  function taskOutputStore(taskId, sessionId = state.currentSessionId) {
    const key = String(sessionId || "") + "\u0000" + String(taskId);
    let store = state.taskOutputStores.get(key);
    if (!store) {
      store = {
        text: "", nextOffset: 0, displayBytes: 0, outputBytes: 0,
        moreOutput: false, hasFetchedDetail: false, status: "", exitCode: null, reason: "",
        agentResult: undefined, pendingApprovals: [], error: "", actionError: "",
        inputBusy: false, cancelBusy: false, outputBusy: false
      };
      state.taskOutputStores.set(key, store);
    }
    return store;
  }

  function stopTaskPolling() {
    if (state.taskPollTimer !== null) {
      window.clearInterval(state.taskPollTimer);
      state.taskPollTimer = null;
    }
    state.taskRequestVersion += 1;
    state.taskLoading = false;
  }

  function startTaskPolling() {
    if (state.activeTab !== "tasks" || !state.currentSessionId || state.taskPollTimer !== null) return;
    state.taskPollTimer = window.setInterval(() => {
      refreshTasks(state.viewVersion);
    }, TASK_POLL_INTERVAL_MS);
  }

  function taskRequestIsCurrent(sessionId, viewVersion, requestVersion) {
    return state.currentSessionId === sessionId && state.viewVersion === viewVersion &&
      state.activeTab === "tasks" && state.taskRequestVersion === requestVersion;
  }

  function renderSessions() {
    sessionList.replaceChildren();
    el("sessionCount").textContent = String(state.sessions.length);
    if (!state.sessions.length) {
      sessionList.append(node("div", "loading-note", "还没有会话"));
      updateWorkspacePresets();
      return;
    }
    const query = sessionSearchInput.value.trim().toLocaleLowerCase();
    const visibleSessions = state.sessions.filter((session) => {
      if (!query) return true;
      return [session.title, session.workspace].some((value) => String(value || "").toLocaleLowerCase().includes(query));
    });
    if (!visibleSessions.length) {
      sessionList.append(node("div", "loading-note", "没有匹配的会话"));
      updateWorkspacePresets();
      return;
    }
    visibleSessions.forEach((session) => {
      const row = node("div", "session-row" + (session.id === state.currentSessionId ? " selected" : ""));
      const main = node("button", "session-select");
      main.type = "button";
      main.setAttribute("aria-current", session.id === state.currentSessionId ? "page" : "false");
      const symbol = node("span", "session-symbol", "◌");
      const copy = node("span", "session-copy");
      copy.append(node("span", "session-name", session.title || "未命名会话"));
      copy.append(node("span", "session-workspace", session.workspace || "未设置工作区"));
      main.append(symbol, copy);
      main.addEventListener("click", () => selectSession(session.id));
      const rename = node("button", "rename-session");
      rename.type = "button";
      rename.title = "重命名会话";
      rename.setAttribute("aria-label", "重命名 " + (session.title || "会话"));
      rename.textContent = "···";
      rename.addEventListener("click", () => beginRename(session, row));
      row.append(main, rename);
      sessionList.append(row);
    });
    updateWorkspacePresets();
  }

  function updateWorkspacePresets() {
    const select = el("workspacePreset");
    const previous = select.value;
    select.replaceChildren();
    const manual = document.createElement("option");
    manual.value = "";
    manual.textContent = "手动输入路径";
    select.append(manual);
    const paths = Array.from(new Set(state.sessions.map((item) => item.workspace).filter(Boolean)));
    paths.forEach((path) => {
      const option = document.createElement("option");
      option.value = path;
      option.textContent = path;
      select.append(option);
    });
    if (paths.includes(previous)) select.value = previous;
  }

  function beginRename(session, row) {
    const main = row.querySelector(".session-select");
    const renameButton = row.querySelector(".rename-session");
    const oldTitle = session.title || "";
    const input = node("input", "rename-input");
    input.value = oldTitle;
    input.maxLength = 120;
    input.setAttribute("aria-label", "新的会话名称");
    main.replaceChildren(input);
    renameButton.textContent = "✓";
    renameButton.title = "保存名称";
    renameButton.setAttribute("aria-label", "保存会话名称");
    let finished = false;
    const finish = async (save) => {
      if (finished) return;
      finished = true;
      if (!save || !input.value.trim()) {
        renderSessions();
        return;
      }
      renameButton.disabled = true;
      try {
        await api(sessionURL(session.id, "/rename"), {
          method: "POST",
          body: { title: input.value.trim() }
        });
        session.title = input.value.trim();
        if (session.id === state.currentSessionId) {
          el("currentSessionTitle").textContent = session.title;
          el("chatHeading").textContent = session.title;
        }
        renderSessions();
        notify("会话名称已更新");
      } catch (error) {
        finished = false;
        renameButton.disabled = false;
        reportError("重命名失败：" + error.message);
        input.focus();
      }
    };
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        finish(true);
      } else if (event.key === "Escape") {
        finish(false);
      }
    });
    input.addEventListener("blur", () => finish(true), { once: true });
    renameButton.onclick = () => finish(true);
    input.focus();
    input.select();
  }

  function addMessage(role, content, extra) {
    const row = node("article", "message-row " + role + "-row");
    const avatar = node("div", "message-avatar", role === "user" ? "我" : role === "tool" ? "↳" : "织");
    const body = node("div", "message-body");
    const author = role === "user" ? "你" : role === "tool" ? "工具" : "Agent";
    body.append(node("div", "message-author", author));
    if (role === "tool") {
      const details = document.createElement("details");
      details.className = "history-tool";
      const summary = node("summary", "", (extra && extra.name) || "工具消息");
      details.append(summary, node("pre", "message-text tool-history-content", content));
      body.append(details);
    } else if (role === "assistant") {
      const text = node("div", "message-text markdown-body");
      if (window.HarnessMarkdown && typeof window.HarnessMarkdown.render === "function") {
        text.append(window.HarnessMarkdown.render(content || ""));
      } else {
        text.textContent = content || "";
      }
      body.append(text);
    } else {
      body.append(node("div", "message-text", content || ""));
    }
    if (extra && extra.timestamp) body.append(node("div", "message-time", extra.timestamp));
    row.append(avatar, body);
    conversation.append(row);
    return row;
  }

  function syncComposer() {
    const session = currentSession();
    const running = state.runOrder.some((id) => {
      const run = state.runs.get(id);
      return run && run.sessionId === state.currentSessionId && run.active;
    });
    const disabled = !session || state.busy || running;
    messageInput.disabled = disabled;
    sendButton.disabled = disabled;
    if (!session) el("composerHint").textContent = "选择一个会话后即可开始";
    else if (state.busy) el("composerHint").textContent = "正在提交任务…";
    else if (running) el("composerHint").textContent = "当前任务完成或取消后可继续发送";
    else el("composerHint").textContent = "当前工作区：" + (session.workspace || "未设置路径");
  }

  function normalizedRole(message) {
    const role = String(message.role || "assistant").toLowerCase();
    if (role === "user" || role === "assistant" || role === "tool") return role;
    return role === "system" ? "tool" : "assistant";
  }

  function addRunDiagnostics(run, value) {
    if (!Array.isArray(run.diagnostics)) run.diagnostics = [];
    const entries = Array.isArray(value) ? value : value && typeof value === "object" ? [value] : [];
    entries.forEach((entry) => {
      if (!entry || typeof entry !== "object") return;
      const key = safeJSON(entry);
      if (!run.diagnostics.some((item) => safeJSON(item) === key)) run.diagnostics.push(entry);
    });
  }

  async function loadRunDiagnostics(run, viewVersion) {
    const requestVersion = (state.diagnosticsRequestVersions.get(run.id) || 0) + 1;
    state.diagnosticsRequestVersions.set(run.id, requestVersion);
    try {
      const data = await api("/api/runs/" + encodeURIComponent(run.id) + "/diagnostics");
      if (viewVersion !== state.viewVersion || run.sessionId !== state.currentSessionId ||
          state.diagnosticsRequestVersions.get(run.id) !== requestVersion) return;
      addRunDiagnostics(run, Array.isArray(data) ? data : []);
      if (run.sessionId === state.currentSessionId) renderConversation();
    } catch (_error) {
      // 历史运行可能尚无诊断记录；运行主体仍可照常恢复。
    }
  }

  function fillAssistantMarkdown(target, text) {
    if (window.HarnessMarkdown && typeof window.HarnessMarkdown.render === "function") {
      target.replaceChildren(window.HarnessMarkdown.render(text || ""));
    } else {
      target.textContent = text || "";
    }
  }

  function updateRunAnswer(run) {
    if (run.sessionId !== state.currentSessionId) return;
    const nearBottom = conversation.scrollHeight - conversation.scrollTop - conversation.clientHeight < 120;
    let answer = run.liveAnswerElement;
    if (!answer || !answer.isConnected) {
      const row = Array.from(conversation.querySelectorAll(".run-row")).find((item) => item.dataset.runId === String(run.id));
      const body = row && row.querySelector(".message-body");
      if (!body) return;
      answer = node("div", "message-text markdown-body live-answer");
      const header = body.querySelector(".run-header");
      body.insertBefore(answer, header ? header.nextSibling : body.firstChild);
      run.liveAnswerElement = answer;
    }
    const content = run.answer || run.text;
    answer.hidden = !content;
    fillAssistantMarkdown(answer, content);
    if (nearBottom) conversation.scrollTop = conversation.scrollHeight;
  }

  function cancelRunTokenRender(run) {
    if (run.tokenFrame !== null && run.tokenFrame !== undefined) {
      window.cancelAnimationFrame(run.tokenFrame);
    }
    run.tokenFrame = null;
    run.tokenRenderVersion = (run.tokenRenderVersion || 0) + 1;
  }

  function scheduleRunTokenRender(run) {
    if (run.tokenFrame !== null && run.tokenFrame !== undefined) return;
    const version = run.tokenRenderVersion || 0;
    run.tokenFrame = window.requestAnimationFrame(() => {
      if ((run.tokenRenderVersion || 0) !== version) return;
      run.tokenFrame = null;
      if (run.sessionId === state.currentSessionId) updateRunAnswer(run);
    });
  }

  function renderRun(run, historyMessages) {
    const row = node("article", "message-row assistant-row run-row");
    row.dataset.runId = String(run.id);
    const avatar = node("div", "message-avatar", "织");
    const body = node("div", "message-body");
    const header = node("div", "run-header");
    header.append(node("div", "message-author", "Agent 运行"));
    const normalizedStatus = String(run.status || "").toLowerCase();
    const statusText = ["waiting_approval", "awaiting_approval", "requires_approval"].includes(normalizedStatus) ? "等待审批" :
      ["done", "completed", "success", "succeeded"].includes(normalizedStatus) ? "已完成" :
        ["cancelled", "canceled"].includes(normalizedStatus) ? "已取消" :
          normalizedStatus === "interrupted" ? "已中断" :
            ["failed", "error"].includes(normalizedStatus) ? "运行失败" :
              ["queued", "pending"].includes(normalizedStatus) ? "排队中" : run.active ? "正在运行" : "任务已结束";
    const stateClass = ["waiting_approval", "awaiting_approval", "requires_approval"].includes(normalizedStatus)
      ? "approval-state"
      : ["done", "completed", "success", "succeeded", "failed", "error", "interrupted", "cancelled", "canceled"].includes(normalizedStatus)
        ? "done-state"
        : "";
    header.append(node("span", "run-state " + stateClass, statusText));
    if (run.active) {
      const cancel = node("button", "cancel-run", "取消任务");
      cancel.type = "button";
      cancel.addEventListener("click", () => cancelRun(run));
      header.append(cancel);
    }
    if (["failed", "cancelled", "interrupted"].includes(normalizedStatus)) {
      const resume = node("button", "resume-run", run.resumeBusy ? "正在继续…" : "继续任务");
      resume.type = "button";
      resume.disabled = Boolean(run.resumeBusy);
      resume.addEventListener("click", () => resumeRun(run));
      header.append(resume);
    }
    body.append(header);

    const hasAnswerInHistory = run.answer && historyMessages.some((message) =>
      normalizedRole(message) === "assistant" && (typeof message.content === "string" ? message.content : safeJSON(message.content)) === run.answer);
    const visibleAnswer = run.answer || run.text;
    if (!hasAnswerInHistory) {
      const answer = node("div", "message-text markdown-body live-answer");
      answer.hidden = !visibleAnswer;
      fillAssistantMarkdown(answer, visibleAnswer);
      run.liveAnswerElement = answer;
      body.append(answer);
    } else {
      run.liveAnswerElement = null;
    }
    if (run.error) body.append(node("div", "run-error", run.error));
    if (["failed", "error"].includes(normalizedStatus) && Array.isArray(run.diagnostics) && run.diagnostics.length) {
      const diagnostics = node("section", "run-diagnostics");
      diagnostics.append(node("div", "run-diagnostics-heading", "诊断建议"));
      run.diagnostics.forEach((diagnostic) => {
        const item = node("article", "run-diagnostic");
        const title = node("div", "run-diagnostic-title");
        if (diagnostic.code) title.append(node("code", "run-diagnostic-code", diagnostic.code));
        title.append(node("strong", "", diagnostic.title || diagnostic.stage || "运行诊断"));
        item.append(title);
        if (diagnostic.message) item.append(node("div", "run-diagnostic-message", diagnostic.message));
        if (diagnostic.suggestion) item.append(node("div", "run-diagnostic-suggestion", "建议：" + diagnostic.suggestion));
        diagnostics.append(item);
      });
      body.append(diagnostics);
    }
    if (normalizedStatus === "interrupted") {
      body.append(node("div", "run-status-note", "继续任务前会先核实工作区实际状态，再从保存的检查点继续。"));
    } else if (normalizedStatus === "waiting_approval") {
      const stage = run.stage ? (typeof run.stage === "string" ? run.stage : safeJSON(run.stage)) : "";
      body.append(node("div", "run-status-note", stage ? "当前阶段：" + stage + "；任务正在等待审批，允许后会从原检查点继续。" : "任务正在等待审批；允许后会从原检查点继续。"));
    }
    if (run.resumeError) body.append(node("div", "run-error", "继续任务失败：" + run.resumeError));

    if (run.tools.length || run.approvals.length) {
      const trace = node("details", "trace-details");
      trace.open = Boolean(run.active);
      trace.append(node("summary", "", "运行轨迹 · " + run.tools.length + " 次工具调用"));
      const events = node("div", "trace-list");
      run.tools.forEach((tool) => {
        const item = node("div", "trace-item");
        const line = node("div", "trace-title");
        line.append(node("span", "trace-icon", tool.done ? "✓" : "↗"));
        line.append(node("strong", "", tool.name || "工具"));
        line.append(node("span", "trace-status", tool.done ? "已返回" : "执行中"));
        item.append(line);
        if (tool.arguments !== undefined) {
          const args = node("details", "trace-payload");
          args.append(node("summary", "", "输入参数"));
          args.append(node("pre", "", safeJSON(tool.arguments)));
          item.append(args);
        }
        if (tool.done) {
          const result = node("details", "trace-payload");
          result.append(node("summary", "", "工具结果"));
          result.append(node("pre", "", safeJSON(tool.result)));
          item.append(result);
        }
        events.append(item);
      });
      run.approvals.forEach((approval) => {
        const card = node("section", "approval-card");
        const heading = node("div", "approval-heading");
        heading.append(node("span", "approval-icon", "◇"), node("strong", "", "需要你的审批"));
        card.append(heading);
        if (approval.action) card.append(node("div", "approval-action", approval.action));
        if (approval.diff !== undefined && approval.diff !== null) {
          card.append(node("pre", "approval-diff", safeJSON(approval.diff)));
        }
        if (approval.error) card.append(node("div", "approval-error", approval.error));
        const approvalActions = node("div", "approval-actions");
        if (approval.status === "pending") {
          const allow = node("button", "allow-button", "允许");
          const reject = node("button", "reject-button", "拒绝");
          allow.type = reject.type = "button";
          allow.disabled = reject.disabled = Boolean(approval.busy);
          allow.addEventListener("click", () => decideApproval(run, approval, true));
          reject.addEventListener("click", () => decideApproval(run, approval, false));
          approvalActions.append(allow, reject);
        } else {
          const approved = ["approved", "allowed"].includes(String(approval.status).toLowerCase());
          approvalActions.append(node("span", "approval-outcome", approved ? "已允许" : "已拒绝"));
        }
        card.append(approvalActions);
        events.append(card);
      });
      trace.append(events);
      body.append(trace);
    }
    row.append(avatar, body);
    conversation.append(row);
  }

  function renderConversation() {
    const nearBottom = conversation.scrollHeight - conversation.scrollTop - conversation.clientHeight < 120;
    conversation.replaceChildren();
    const messages = Array.isArray(state.messages) ? state.messages : [];
    const sessionRuns = state.runOrder.map((id) => state.runs.get(id)).filter((run) => run && run.sessionId === state.currentSessionId);
    const pendingTexts = sessionRuns.filter((run) => run.userText).map((run) => run.userText);
    const shownPending = new Set();
    messages.forEach((message) => {
      const role = normalizedRole(message);
      const content = typeof message.content === "string" ? message.content : safeJSON(message.content);
      if (role === "assistant" && !content && message.tool_calls) return;
      if (role === "user") {
        const pendingIndex = pendingTexts.indexOf(content);
        if (pendingIndex >= 0) shownPending.add(pendingIndex);
      }
      addMessage(role, content, { name: message.name || message.tool_name, timestamp: message.timestamp });
    });
    sessionRuns.forEach((run) => {
      if (run.userText && !messages.some((message) => normalizedRole(message) === "user" && String(message.content || "") === run.userText)) {
        addMessage("user", run.userText);
      }
      renderRun(run, messages);
    });
    const hasContent = messages.length > 0 || sessionRuns.length > 0;
    emptyState.hidden = hasContent;
    if (!hasContent) conversation.append(emptyState);
    if (nearBottom || !hasContent) conversation.scrollTop = conversation.scrollHeight;
    syncComposer();
  }

  async function selectSession(id) {
    const session = state.sessions.find((item) => item.id === id);
    if (!session) return;
    saveSessionDraft(state.currentSessionId, messageInput.value);
    closeGitRestoreModal();
    stopTaskPolling();
    state.currentSessionId = id;
    messageInput.value = readSessionDraft(id);
    resizeComposer();
    state.taskSessionId = id;
    state.tasks = [];
    state.taskError = "";
    rememberSession(id);
    state.viewVersion += 1;
    state.fileRequestVersion += 1;
    const version = state.viewVersion;
    state.messages = [];
    state.memories = [];
    state.editingMemoryId = null;
    state.files = [];
    state.selectedFile = null;
    state.searchResults = null;
    state.indexSummary = null;
    state.git = { sessionId: id, status: null, diff: null, snapshots: [], loading: false, errors: [], snapshotBusy: false };
    state.gitPreview = null;
    el("currentSessionTitle").textContent = session.title || "未命名会话";
    el("chatHeading").textContent = session.title || "工作会话";
    el("workspacePath").textContent = session.workspace || "未设置工作区路径";
    messageInput.disabled = false;
    sendButton.disabled = false;
    el("composerHint").textContent = "当前工作区：" + (session.workspace || "未设置路径");
    renderSessions();
    renderConversation();
    renderContext();
    if (state.activeTab === "tasks") {
      startTaskPolling();
      refreshTasks(version);
    }
    closeMobileSidebar();
    try {
      const messages = await api(sessionURL(id, "/messages"));
      if (version !== state.viewVersion) return;
      state.messages = Array.isArray(messages) ? messages : (messages && Array.isArray(messages.messages) ? messages.messages : []);
      renderConversation();
    } catch (error) {
      if (version === state.viewVersion) reportError("读取会话消息失败：" + error.message);
    }
    loadMemories(version);
    loadFiles(version);
    if (state.activeTab === "git") loadGit(version);
    recoverRuns(id, version);
  }

  async function loadSessions(preferredId) {
    const data = await api("/api/sessions");
    state.sessions = Array.isArray(data) ? data : (data && Array.isArray(data.sessions) ? data.sessions : []);
    renderSessions();
    const target = preferredId && state.sessions.find((item) => item.id === preferredId)
      ? preferredId
      : state.sessions.some((item) => item.id === storedSessionId())
        ? storedSessionId()
      : state.sessions.some((item) => item.id === state.currentSessionId)
        ? state.currentSessionId
        : state.sessions.length ? state.sessions[0].id : null;
    if (target) await selectSession(target);
    else {
      closeGitRestoreModal();
      stopTaskPolling();
      state.currentSessionId = null;
      state.taskSessionId = null;
      state.tasks = [];
      state.taskError = "";
      state.messages = [];
      state.git = { sessionId: null, status: null, diff: null, snapshots: [], loading: false, errors: [], snapshotBusy: false };
      state.gitPreview = null;
      renderConversation();
      renderContext();
      el("currentSessionTitle").textContent = "选择一个会话";
      el("chatHeading").textContent = "你好，今天想完成什么？";
      el("workspacePath").textContent = "创建一个会话并选择工作区，开始与 Agent 协作。";
      messageInput.disabled = true;
      sendButton.disabled = true;
      el("composerHint").textContent = "选择一个会话后即可开始";
    }
  }

  async function recoverRuns(sessionId, version) {
    try {
      const data = await api("/api/runs");
      const runs = Array.isArray(data) ? data : (data && Array.isArray(data.runs) ? data.runs : []);
      const activeStatuses = new Set(["queued", "running", "pending", "waiting_approval", "awaiting_approval", "requires_approval"]);
      const matches = runs
        .filter((run) => (run.session_id || run.sessionId) === sessionId)
        .sort((left, right) => String(left.created_at || left.createdAt || "").localeCompare(String(right.created_at || right.createdAt || "")))
        .slice(-20);
      matches.forEach((run) => {
        const id = String(run.id);
        let item = state.runs.get(id);
        if (!item) {
          const message = run.message;
          const userText = typeof message === "string" ? message : message && typeof message.content === "string" ? message.content : "";
          item = {
            id, sessionId, status: run.status, active: false, text: "",
            answer: "", error: "", userText, tools: [], approvals: [], diagnostics: [], source: null,
            lastEventId: 0, historyLoaded: false
          };
          state.runs.set(id, item);
          state.runOrder.push(id);
        }
        item.sessionId = sessionId;
        item.status = run.status;
        item.active = activeStatuses.has(String(run.status).toLowerCase());
        item.answer = String(run.answer || item.answer || "");
        item.error = String(run.error || item.error || "");
        if (item.active || !item.historyLoaded) connectRun(item);
        if (item.active || String(run.status).toLowerCase() === "waiting_approval") restoreApprovals(item);
        loadRunDiagnostics(item, version);
      });
      if (version === state.viewVersion) renderConversation();
    } catch (error) {
      if (version === state.viewVersion) reportError("恢复运行中任务失败：" + error.message);
    }
  }

  async function restoreApprovals(run) {
    try {
      const data = await api("/api/runs/" + encodeURIComponent(run.id) + "/approvals");
      const approvals = Array.isArray(data) ? data : (data && Array.isArray(data.approvals) ? data.approvals : []);
      approvals.forEach((approval) => {
        const id = String(approval.id);
        const existing = run.approvals.find((item) => item.id === id);
        if (!existing) {
          run.approvals.push({
            id,
            action: approval.action,
            diff: approval.diff,
            status: ["approved", "allowed", "rejected"].includes(String(approval.status).toLowerCase()) ? approval.status : "pending"
          });
        }
      });
      if (run.sessionId === state.currentSessionId) renderConversation();
    } catch (error) {
      reportError("恢复审批状态失败：" + error.message);
    }
  }

  function connectRun(run) {
    if (run.source || run.historyLoaded || typeof EventSource === "undefined") {
      if (typeof EventSource === "undefined") reportError("当前浏览器不支持实时事件流。");
      return;
    }
    setStreamStatus("连接任务事件…", "connecting");
    const after = Number(run.lastEventId || 0);
    const suffix = after > 0 ? "?after=" + encodeURIComponent(String(after)) : "";
    const source = new EventSource("/api/runs/" + encodeURIComponent(run.id) + "/events" + suffix, { withCredentials: true });
    run.source = source;
    const receive = (event) => {
      let message;
      try {
        message = JSON.parse(event.data);
      } catch (_error) {
        reportError("任务 " + run.id + " 返回了无法解析的事件。");
        return;
      }
      handleRunEvent(run, message);
    };
    source.onopen = () => {
      setStreamStatus("实时事件已连接", "online");
      setAPIStatus("服务已连接", "online");
    };
    source.onmessage = receive;
    ["token", "tool_start", "tool_result", "approval", "paused", "diagnostic", "done"].forEach((name) => source.addEventListener(name, receive));
    source.onerror = () => {
      if (run.active) setStreamStatus("连接中断，正在自动重连…", "reconnecting");
      setAPIStatus("连接恢复中", "reconnecting");
    };
  }

  function handleRunEvent(run, event) {
    if (!event || typeof event !== "object") return;
    const eventId = Number(event.id);
    if (Number.isSafeInteger(eventId) && eventId > 0) {
      if (eventId <= Number(run.lastEventId || 0)) return;
      run.lastEventId = eventId;
    }
    const payload = event.payload || {};
    if (event.kind !== "token") cancelRunTokenRender(run);
    if (event.kind === "token") {
      run.text += String(payload.text || "");
    } else if (event.kind === "tool_start") {
      const previous = payload.call_key && run.tools.find((item) => item.callKey === payload.call_key);
      if (!previous) run.tools.push({ name: payload.name, arguments: payload.arguments, callKey: payload.call_key, done: false });
    } else if (event.kind === "tool_result") {
      const tool = [...run.tools].reverse().find((item) => item.name === payload.name && !item.done);
      if (tool) {
        tool.result = payload.result;
        tool.done = true;
      } else {
        run.tools.push({ name: payload.name, result: payload.result, done: true });
      }
    } else if (event.kind === "approval") {
      const id = String(payload.id || event.id || "");
      let approval = run.approvals.find((item) => item.id === id);
      if (!approval) {
        approval = { id, status: "pending" };
        run.approvals.push(approval);
      }
      approval.action = payload.action;
      approval.diff = payload.diff;
      run.status = "waiting_approval";
      run.active = true;
      setStreamStatus("等待审批", "online");
    } else if (event.kind === "paused") {
      run.status = "waiting_approval";
      run.active = true;
      run.stage = payload.stage || payload.message || "等待审批";
      setStreamStatus("等待审批", "online");
    } else if (event.kind === "diagnostic") {
      addRunDiagnostics(run, payload.diagnostic !== undefined ? payload.diagnostic : payload);
    } else if (event.kind === "done") {
      run.status = String(payload.status || (payload.error ? "failed" : "succeeded")).toLowerCase();
      const activeStatuses = new Set(["queued", "running", "pending", "waiting_approval", "awaiting_approval", "requires_approval"]);
      run.active = activeStatuses.has(run.status);
      if (payload.answer !== undefined) run.answer = String(payload.answer || "");
      if (payload.error !== undefined) run.error = String(payload.error || "");
      if (payload.diagnostic !== undefined) addRunDiagnostics(run, payload.diagnostic);
      if (!run.active && run.source) {
        run.source.close();
        run.source = null;
      }
      if (!run.active) run.historyLoaded = true;
      setStreamStatus(run.status === "waiting_approval" ? "等待审批" : run.active ? "任务运行中" : "等待任务", run.active ? "online" : "");
      if (!run.active) refreshMessages(run);
    }
    if (run.sessionId === state.currentSessionId) {
      if (event.kind === "token") scheduleRunTokenRender(run);
      else renderConversation();
    }
  }

  async function refreshMessages(run) {
    try {
      const messages = await api(sessionURL(run.sessionId, "/messages"));
      if (Array.isArray(messages)) {
        if (run.sessionId === state.currentSessionId) {
          state.messages = messages;
          renderConversation();
        }
      }
    } catch (_error) {
      if (run.sessionId === state.currentSessionId) {
        state.messages = state.messages || [];
        renderConversation();
      }
    }
  }

  async function cancelRun(run) {
    try {
      await api("/api/runs/" + encodeURIComponent(run.id) + "/cancel", { method: "POST" });
      run.status = "cancelling";
      if (run.sessionId === state.currentSessionId) renderConversation();
      notify("已发送取消请求");
    } catch (error) {
      reportError("取消任务失败：" + error.message);
    }
  }

  async function decideApproval(run, approval, allow) {
    if (approval.busy) return;
    approval.busy = true;
    renderConversation();
    try {
      const result = await api("/api/approvals/" + encodeURIComponent(approval.id), {
        method: "POST",
        body: { allow }
      });
      approval.status = result && result.status
        ? String(result.status).toLowerCase()
        : allow ? "approved" : "rejected";
      run.status = "running";
      run.active = true;
      connectRun(run);
      setStreamStatus("任务继续中", "online");
      approval.busy = false;
      reportError("");
      if (run.sessionId === state.currentSessionId) renderConversation();
      notify(allow ? "已允许此操作" : "已拒绝此操作");
    } catch (error) {
      approval.busy = false;
      approval.error = error.message;
      if (run.sessionId === state.currentSessionId) renderConversation();
    }
  }

  async function resumeRun(run) {
    if (run.resumeBusy) return;
    run.resumeBusy = true;
    run.resumeError = "";
    if (run.sessionId === state.currentSessionId) renderConversation();
    try {
      const result = await api("/api/runs/" + encodeURIComponent(run.id) + "/resume", {
        method: "POST",
        body: {}
      });
      const resumed = result && result.run ? result.run : result;
      if (!resumed || resumed.id === undefined || resumed.id === null) throw new Error("服务没有返回新的任务编号");
      const id = String(resumed.id);
      const activeStatuses = new Set(["queued", "running", "pending", "waiting_approval", "awaiting_approval", "requires_approval"]);
      const status = String(resumed.status || "queued").toLowerCase();
      let item = state.runs.get(id);
      if (!item) {
        item = {
          id, sessionId: run.sessionId, status, active: activeStatuses.has(status),
          text: "", answer: String(resumed.answer || ""), error: String(resumed.error || ""),
          userText: run.userText || "", tools: [], approvals: [], source: null,
          lastEventId: 0, historyLoaded: false
        };
        state.runs.set(id, item);
        state.runOrder.push(id);
      }
      item.status = status;
      item.active = activeStatuses.has(status);
      item.resumeBusy = false;
      connectRun(item);
      if (item.sessionId === state.currentSessionId) renderConversation();
      notify("已创建续接任务；Agent 将先核实实际状态，不重放旧工具");
    } catch (error) {
      run.resumeBusy = false;
      run.resumeError = error.message;
      if (run.sessionId === state.currentSessionId) renderConversation();
    }
  }

  async function submitMessage(message) {
    const session = currentSession();
    if (!session || state.busy || !message.trim() || state.runOrder.some((id) => {
      const activeRun = state.runs.get(id);
      return activeRun && activeRun.sessionId === session.id && activeRun.active;
    })) return;
    saveSessionDraft(session.id, message);
    state.busy = true;
    syncComposer();
    reportError("");
    const run = {
      id: "pending-" + Date.now(),
      sessionId: session.id,
      status: "queued",
      active: true,
      text: "",
      answer: "",
      error: "",
      userText: message.trim(),
      tools: [],
      approvals: [],
      source: null
    };
    state.runs.set(run.id, run);
    state.runOrder.push(run.id);
    renderConversation();
    setStreamStatus("提交任务…", "connecting");
    try {
      const response = await api(sessionURL(session.id, "/runs"), {
        method: "POST",
        body: { message: message.trim() }
      });
      saveSessionDraft(session.id, "");
      if (state.currentSessionId === session.id) {
        messageInput.value = "";
        resizeComposer();
      }
      const actualId = String(response.id);
      const pendingId = run.id;
      state.runs.delete(run.id);
      run.id = actualId;
      run.status = response.status || "running";
      state.runs.set(run.id, run);
      const pendingIndex = state.runOrder.findIndex((id) => id === pendingId);
      if (pendingIndex >= 0) state.runOrder[pendingIndex] = run.id;
      connectRun(run);
      renderConversation();
    } catch (error) {
      run.active = false;
      run.status = "error";
      run.error = error.message;
      saveSessionDraft(session.id, message);
      if (state.currentSessionId === session.id) {
        messageInput.value = message;
        resizeComposer();
      }
      reportError("提交任务失败：" + error.message);
      renderConversation();
    } finally {
      state.busy = false;
      syncComposer();
      if (state.currentSessionId === session.id) messageInput.focus();
    }
  }

  function renderContext() {
    contextContent.replaceChildren();
    const session = currentSession();
    const tabs = document.querySelectorAll(".context-tab");
    tabs.forEach((tab) => {
      const active = tab.dataset.tab === state.activeTab;
      tab.classList.toggle("active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });
    if (!session) {
      contextContent.append(node("div", "context-empty", "创建或选择会话后，这里会显示工作区内容。"));
      return;
    }
    if (state.activeTab === "files") renderFilesPanel();
    else if (state.activeTab === "search") renderSearchPanel();
    else if (state.activeTab === "memories") renderMemoriesPanel();
    else if (state.activeTab === "git") renderGitPanel();
    else if (state.activeTab === "tasks") renderTasksPanel();
  }

  function taskIdentifier(task) {
    const value = task && (task.task_id ?? task.id);
    return value === undefined || value === null ? "" : String(value);
  }

  function pendingApprovalsFrom(source) {
    if (!source || typeof source !== "object") return null;
    const status = source.status && typeof source.status === "object" ? source.status : null;
    const task = source.task && typeof source.task === "object" ? source.task : null;
    const taskStatus = task && task.status && typeof task.status === "object" ? task.status : null;
    const candidates = [
      source.pending_approvals,
      status && status.pending_approvals,
      task && task.pending_approvals,
      taskStatus && taskStatus.pending_approvals
    ];
    return candidates.find(Array.isArray) || null;
  }

  function updateTaskPendingApprovals(source, store) {
    const approvals = pendingApprovalsFrom(source);
    if (!approvals) return;
    const previous = new Map((store.pendingApprovals || []).map((approval) => [approval.id, approval]));
    store.pendingApprovals = approvals
      .filter((approval) => approval && typeof approval === "object" && approval.id !== undefined && approval.id !== null)
      .map((approval) => {
        const id = String(approval.id);
        const existing = previous.get(id);
        return {
          ...approval,
          id,
          status: String(approval.status || "pending"),
          busy: Boolean(existing && existing.busy),
          error: existing && existing.error ? existing.error : ""
        };
      });
  }

  function taskIsTerminal(task, store) {
    const status = String((store && store.status) || task.state || "").toLowerCase();
    return ["done", "completed", "success", "succeeded", "failed", "error", "cancelled", "canceled", "stopped", "finished", "exited", "interrupted"].includes(status) ||
      (store && store.exitCode !== null && store.exitCode !== undefined) ||
      (task.exit_code !== null && task.exit_code !== undefined);
  }

  function taskStatusText(status) {
    const labels = {
      queued: "排队中", starting: "启动中", running: "运行中", waiting_input: "等待输入",
      waiting_for_input: "等待输入", paused: "已暂停", cancelling: "正在取消",
      done: "已完成", completed: "已完成", success: "已完成", succeeded: "已完成",
      failed: "失败", error: "失败", cancelled: "已取消", canceled: "已取消",
      stopped: "已停止", finished: "已结束", exited: "已退出", interrupted: "已中断"
    };
    const value = String(status || "未知");
    return labels[value.toLowerCase()] || value;
  }

  function taskBytesText(value) {
    const bytes = Number(value);
    return Number.isFinite(bytes) && bytes >= 0 ? bytes.toLocaleString("zh-CN") + " 字节" : "未知";
  }

  function renderTasksPanel() {
    const toolbar = node("div", "panel-toolbar task-toolbar");
    const label = node("div", "panel-title");
    label.append(node("span", "panel-icon", "▣"), node("strong", "", "终端任务"));
    const refresh = node("button", "subtle-button", state.taskLoading ? "读取中…" : "刷新");
    refresh.type = "button";
    refresh.disabled = state.taskLoading;
    refresh.addEventListener("click", () => refreshTasks(state.viewVersion));
    toolbar.append(label, refresh);
    contextContent.append(toolbar);
    contextContent.append(node("div", "task-panel-hint", "任务由 Agent 的 start_pty 或 spawn_agent 工具发起。工具运行结束或暂停时，任务会继续运行。"));
    if (state.taskError) contextContent.append(node("div", "task-error", state.taskError));
    if (!state.tasks.length) {
      contextContent.append(node("div", "context-empty", state.taskLoading ? "正在读取此会话的任务…" : "此会话还没有终端任务。"));
      return;
    }
    const list = node("div", "task-list");
    state.tasks.forEach((task) => {
      const id = taskIdentifier(task);
      if (!id) return;
      const sessionId = state.currentSessionId;
      const viewVersion = state.viewVersion;
      const store = taskOutputStore(id, sessionId);
      const card = node("article", "task-card");
      const header = node("div", "task-card-header");
      const title = node("div", "task-card-title");
      title.append(node("strong", "", task.kind || "终端任务"), node("code", "task-id", id));
      header.append(title, node("span", "task-state", taskStatusText(store.status || task.state)));
      const actions = node("div", "task-actions");
      if (!taskIsTerminal(task, store)) {
        const cancel = node("button", "task-cancel-button", store.cancelBusy ? "正在取消…" : "取消任务");
        cancel.type = "button";
        cancel.disabled = store.cancelBusy;
        cancel.addEventListener("click", () => cancelTerminalTask(state.currentSessionId, id));
        actions.append(cancel);
      }
      card.append(header);
      const meta = node("dl", "task-meta");
      const exitCode = store.exitCode !== null && store.exitCode !== undefined ? store.exitCode : task.exit_code;
      const reason = store.reason || task.reason;
      const outputBytes = store.outputBytes || task.output_bytes;
      [
        ["退出码", exitCode === undefined || exitCode === null ? "—" : String(exitCode)],
        ["原因", reason || "—"],
        ["输出大小", taskBytesText(outputBytes)]
      ].forEach(([key, value]) => {
        const row = node("div", "task-meta-row");
        row.append(node("dt", "", key), node("dd", "", value));
        meta.append(row);
      });
      card.append(meta);
      if (store.pendingApprovals.length) {
        const approvalList = node("section", "task-approval-list");
        store.pendingApprovals.forEach((approval) => {
          const approvalCard = node("section", "task-approval-card");
          const approvalHeader = node("div", "task-approval-header");
          approvalHeader.append(node("strong", "", "子代理请求审批"), node("code", "task-approval-id", approval.id));
          approvalCard.append(approvalHeader);
          approvalCard.append(node("div", "task-approval-field", "操作：" + String(approval.action || "—")));
          approvalCard.append(node("div", "task-approval-field", "目标：" + String(approval.target || "—")));
          const details = node("pre", "task-approval-details");
          details.textContent = safeJSON(approval.details);
          approvalCard.append(details);
          const approvalActions = node("div", "task-approval-actions");
          const approvalStatus = String(approval.status || "pending").toLowerCase();
          const terminal = taskIsTerminal(task, store);
          if (approvalStatus === "pending") {
            const allow = node("button", "task-approval-allow", approval.busy ? "处理中…" : "允许");
            allow.type = "button";
            allow.setAttribute("aria-label", "允许子代理修改 " + approval.id);
            allow.disabled = Boolean(approval.busy || terminal || !sessionId);
            allow.addEventListener("click", () => decideTaskApproval(sessionId, id, approval.id, true, viewVersion));
            const reject = node("button", "task-approval-reject", approval.busy ? "处理中…" : "拒绝");
            reject.type = "button";
            reject.setAttribute("aria-label", "拒绝子代理修改 " + approval.id);
            reject.disabled = Boolean(approval.busy || terminal || !sessionId);
            reject.addEventListener("click", () => decideTaskApproval(sessionId, id, approval.id, false, viewVersion));
            approvalActions.append(allow, reject);
            if (terminal) approvalCard.append(node("div", "task-approval-ended", "任务已结束，此审批不可操作。"));
          } else {
            const approved = ["approved", "allowed"].includes(approvalStatus);
            approvalActions.append(node("span", "task-approval-outcome", approved ? "已允许" : "已拒绝"));
          }
          if (approval.error) approvalCard.append(node("div", "task-error", approval.error));
          approvalCard.append(approvalActions);
          approvalList.append(approvalCard);
        });
        card.append(approvalList);
      }
      const outputHeading = node("div", "task-output-heading", "终端输出");
      card.append(outputHeading);
      card.append(node("pre", "task-output", store.text || (store.error ? "读取输出失败。" : "暂无输出。")));
      if (store.moreOutput && store.displayBytes < TASK_OUTPUT_TOTAL_BYTES) {
        const readMore = node("button", "subtle-button task-read-more", store.outputBusy ? "读取中…" : "读取更多输出");
        readMore.type = "button";
        readMore.disabled = store.outputBusy || state.taskLoading;
        readMore.addEventListener("click", () => readMoreTaskOutput(state.currentSessionId, id));
        card.append(readMore);
      }
      if (store.displayBytes >= TASK_OUTPUT_TOTAL_BYTES) {
        card.append(node("div", "task-output-limit", "客户端显示上限为 64 KiB，后续输出不再追加。"));
      }
      if (store.error) card.append(node("div", "task-error", store.error));
      if (store.agentResult !== undefined && store.agentResult !== null) {
        const result = node("details", "task-agent-result");
        result.append(node("summary", "", "agent_result（结构化数据，仅展示）"));
        result.append(node("pre", "", safeJSON(store.agentResult)));
        card.append(result);
      }
      if (!taskIsTerminal(task, store) && task.kind === "pty") {
        const inputLabel = node("label", "task-input-label", "向终端发送输入");
        const input = node("textarea", "text-input task-input");
        input.dataset.taskInputId = id;
        input.rows = 2;
        input.placeholder = "输入要发送给运行程序的文本…";
        input.setAttribute("aria-label", "发送终端输入到任务 " + id);
        input.value = state.taskInputDrafts.get(id) || "";
        input.addEventListener("input", () => state.taskInputDrafts.set(id, input.value));
        card.append(inputLabel, input);
        card.append(node("div", "task-input-warning", "终端输入会影响当前运行程序，可能触发命令、提交内容或改变程序状态。只有点击确认按钮后才会发送。"));
        const send = node("button", "primary-button task-input-confirm", store.inputBusy ? "发送中…" : "确认并发送输入");
        send.type = "button";
        send.disabled = store.inputBusy;
        send.addEventListener("click", () => sendTerminalInput(state.currentSessionId, id, input));
        actions.append(send);
      }
      if (store.actionError) card.append(node("div", "task-error", store.actionError));
      if (actions.childElementCount) card.append(actions);
      list.append(card);
    });
    contextContent.append(list);
  }

  function renderTasksPanelPreservingFocus() {
    const active = document.activeElement;
    const inputId = active && active.dataset ? active.dataset.taskInputId : null;
    const selectionStart = inputId && typeof active.selectionStart === "number" ? active.selectionStart : null;
    const selectionEnd = inputId && typeof active.selectionEnd === "number" ? active.selectionEnd : null;
    const scrollTop = contextContent.scrollTop;
    renderContext();
    contextContent.scrollTop = scrollTop;
    if (!inputId) return;
    const input = Array.from(contextContent.querySelectorAll("[data-task-input-id]")).find((item) => item.dataset.taskInputId === inputId);
    if (input) {
      input.focus();
      if (selectionStart !== null && selectionEnd !== null) input.setSelectionRange(selectionStart, selectionEnd);
    }
  }

  async function readTaskDetail(sessionId, task, viewVersion, requestVersion) {
    const id = taskIdentifier(task);
    if (!id || !taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) return;
    const store = taskOutputStore(id, sessionId);
    updateTaskStoreFromList(task, store);
    const offset = Math.max(0, Number(store.nextOffset) || 0);
    try {
      const detail = await api(taskURL(sessionId, id) + "?offset=" + encodeURIComponent(String(offset)));
      if (!taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) return;
      if (!detail || typeof detail !== "object") throw new Error("任务详情格式无效");
      if (detail.ok === false) throw new Error(detail.error || detail.reason || "读取任务详情失败");
      if (detail && detail.state !== undefined) store.status = detail.state;
      if (detail && Object.prototype.hasOwnProperty.call(detail, "exit_code")) store.exitCode = detail.exit_code;
      if (detail && Object.prototype.hasOwnProperty.call(detail, "reason")) store.reason = detail.reason || "";
      if (detail && Object.prototype.hasOwnProperty.call(detail, "output_bytes")) store.outputBytes = Number(detail.output_bytes) || 0;
      if (detail && Object.prototype.hasOwnProperty.call(detail, "agent_result")) store.agentResult = detail.agent_result;
      updateTaskPendingApprovals(detail, store);
      const rawOutput = typeof detail.output === "string" ? detail.output : detail.output == null ? "" : safeJSON(detail.output);
      const chunk = truncateUtf8(rawOutput, TASK_OUTPUT_CHUNK_BYTES);
      const chunkBytes = utf8Length(chunk);
      const rawBytes = utf8Length(rawOutput);
      const remainingBytes = Math.max(0, TASK_OUTPUT_TOTAL_BYTES - store.displayBytes);
      const visible = truncateUtf8(chunk, remainingBytes);
      store.text += visible;
      store.displayBytes += utf8Length(visible);
      const reportedNextOffset = Number(detail.next_offset);
      store.nextOffset = chunkBytes < rawBytes
        ? offset + chunkBytes
        : Number.isFinite(reportedNextOffset) ? Math.max(offset, reportedNextOffset) : offset + rawBytes;
      store.moreOutput = Boolean(detail.more_output) || chunkBytes < rawBytes;
      store.hasFetchedDetail = true;
      store.error = "";
    } catch (error) {
      if (taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) store.error = error.message;
    }
  }

  function updateTaskStoreFromList(task, store = taskOutputStore(taskIdentifier(task))) {
    if (task.state !== undefined) store.status = task.state || store.status;
    if (task.exit_code !== undefined) store.exitCode = task.exit_code;
    if (task.reason !== undefined) store.reason = task.reason || "";
    if (task.output_bytes !== undefined) store.outputBytes = Number(task.output_bytes) || 0;
    if (Object.prototype.hasOwnProperty.call(task, "agent_result")) store.agentResult = task.agent_result;
    updateTaskPendingApprovals(task, store);
  }

  async function refreshTasks(viewVersion = state.viewVersion) {
    const sessionId = state.currentSessionId;
    if (!sessionId || state.activeTab !== "tasks" || state.taskLoading) return;
    state.taskLoading = true;
    state.taskError = "";
    state.taskSessionId = sessionId;
    const requestVersion = ++state.taskRequestVersion;
    try {
      const data = await api(sessionURL(sessionId, "/tasks"));
      if (!taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) return;
      if (data && data.ok === false) throw new Error(data.error || data.reason || "读取任务列表失败");
      state.tasks = unwrapList(data, "tasks");
      await Promise.all(state.tasks.map((task) => {
        const store = taskOutputStore(taskIdentifier(task), sessionId);
        updateTaskStoreFromList(task, store);
        const hasPendingApproval = store.pendingApprovals.some((approval) => String(approval.status || "pending").toLowerCase() === "pending");
        return !store.hasFetchedDetail || !taskIsTerminal(task, store) || hasPendingApproval
          ? readTaskDetail(sessionId, task, viewVersion, requestVersion)
          : Promise.resolve();
      }));
    } catch (error) {
      if (taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) state.taskError = error.message;
    } finally {
      if (state.taskRequestVersion === requestVersion) {
        state.taskLoading = false;
        if (taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) renderTasksPanelPreservingFocus();
      }
    }
  }

  async function readMoreTaskOutput(sessionId, taskId) {
    if (!sessionId || state.currentSessionId !== sessionId || state.activeTab !== "tasks" || state.taskLoading) return;
    const task = state.tasks.find((item) => taskIdentifier(item) === taskId);
    const store = taskOutputStore(taskId, sessionId);
    if (!task || !store.moreOutput || store.outputBusy) return;
    const viewVersion = state.viewVersion;
    const requestVersion = ++state.taskRequestVersion;
    state.taskLoading = true;
    store.outputBusy = true;
    try {
      await readTaskDetail(sessionId, task, viewVersion, requestVersion);
    } finally {
      store.outputBusy = false;
      if (state.taskRequestVersion === requestVersion) {
        state.taskLoading = false;
        if (taskRequestIsCurrent(sessionId, viewVersion, requestVersion)) renderTasksPanelPreservingFocus();
      }
    }
  }

  function taskApprovalActionIsCurrent(sessionId, taskId, viewVersion) {
    return Boolean(sessionId && state.currentSessionId === sessionId && state.taskSessionId === sessionId &&
      state.viewVersion === viewVersion && state.activeTab === "tasks" &&
      state.tasks.some((task) => taskIdentifier(task) === taskId));
  }

  async function decideTaskApproval(sessionId, taskId, approvalId, allow, viewVersion) {
    if (!taskApprovalActionIsCurrent(sessionId, taskId, viewVersion)) return;
    const task = state.tasks.find((item) => taskIdentifier(item) === taskId);
    const store = taskOutputStore(taskId, sessionId);
    const approval = store.pendingApprovals.find((item) => item.id === approvalId);
    if (!task || !approval || String(approval.status || "pending").toLowerCase() !== "pending" ||
        approval.busy || taskIsTerminal(task, store)) return;
    approval.busy = true;
    approval.error = "";
    try {
      const result = await api(taskURL(sessionId, taskId, "/approvals/" + encodeURIComponent(approvalId)), {
        method: "POST",
        body: { allow }
      });
      if (!taskApprovalActionIsCurrent(sessionId, taskId, viewVersion)) return;
      if (result && result.ok === false) throw new Error(result.error || result.reason || "提交审批结果失败");
      const current = taskOutputStore(taskId, sessionId).pendingApprovals.find((item) => item.id === approvalId);
      if (current) {
        const reportedStatus = result && String(result.status || "").toLowerCase();
        current.status = ["approved", "allowed", "rejected"].includes(reportedStatus)
          ? reportedStatus
          : allow ? "approved" : "rejected";
        current.error = "";
      }
      notify(allow ? "已允许子代理请求" : "已拒绝子代理请求");
    } catch (error) {
      if (taskApprovalActionIsCurrent(sessionId, taskId, viewVersion)) {
        const current = taskOutputStore(taskId, sessionId).pendingApprovals.find((item) => item.id === approvalId);
        if (current) current.error = error.message;
      }
    } finally {
      const current = taskOutputStore(taskId, sessionId).pendingApprovals.find((item) => item.id === approvalId);
      if (current) current.busy = false;
      if (taskApprovalActionIsCurrent(sessionId, taskId, viewVersion)) {
        renderTasksPanelPreservingFocus();
        await refreshTasks(viewVersion);
      }
    }
  }

  async function sendTerminalInput(sessionId, taskId, input) {
    const text = input.value;
    if (!sessionId || !text || state.taskSessionId !== sessionId) return;
    const store = taskOutputStore(taskId, sessionId);
    if (store.inputBusy) return;
    store.inputBusy = true;
    store.actionError = "";
    const viewVersion = state.viewVersion;
    try {
      const result = await api(taskURL(sessionId, taskId, "/input"), {
        method: "POST",
        body: { text, allow: true }
      });
      if (result && result.ok === false) throw new Error(result.error || result.reason || "发送终端输入失败");
      if (state.currentSessionId !== sessionId || state.viewVersion !== viewVersion) return;
      if (state.taskInputDrafts.get(taskId) === text) state.taskInputDrafts.delete(taskId);
      notify("终端输入已发送");
    } catch (error) {
      if (state.currentSessionId === sessionId && state.viewVersion === viewVersion) store.actionError = error.message;
    } finally {
      store.inputBusy = false;
      if (state.activeTab === "tasks" && state.currentSessionId === sessionId && state.viewVersion === viewVersion) {
        await refreshTasks(viewVersion);
      }
    }
  }

  async function cancelTerminalTask(sessionId, taskId) {
    if (!sessionId || state.taskSessionId !== sessionId) return;
    const store = taskOutputStore(taskId, sessionId);
    if (store.cancelBusy) return;
    store.cancelBusy = true;
    store.actionError = "";
    const viewVersion = state.viewVersion;
    try {
      const result = await api(taskURL(sessionId, taskId, "/cancel"), {
        method: "POST",
        body: { allow: true }
      });
      if (result && result.ok === false) throw new Error(result.error || result.reason || "取消任务失败");
      if (state.currentSessionId === sessionId && state.viewVersion === viewVersion) notify("已发送任务取消请求");
    } catch (error) {
      if (state.currentSessionId === sessionId && state.viewVersion === viewVersion) store.actionError = error.message;
    } finally {
      store.cancelBusy = false;
      if (state.activeTab === "tasks" && state.currentSessionId === sessionId && state.viewVersion === viewVersion) {
        await refreshTasks(viewVersion);
      }
    }
  }

  function unwrapList(data, key) {
    if (Array.isArray(data)) return data;
    return data && Array.isArray(data[key]) ? data[key] : [];
  }

  function gitDisplayValue(value) {
    if (value === null || value === undefined || value === "") return "无";
    if (typeof value === "boolean") return value ? "是" : "否";
    if (Array.isArray(value)) {
      return value.map((item) => {
        if (typeof item === "string") return item;
        if (!item || typeof item !== "object") return String(item);
        return item.path || item.relative_path || item.name || safeJSON(item);
      }).join("、") || "无";
    }
    if (typeof value === "object") return safeJSON(value);
    return String(value);
  }

  function gitDiffText(value) {
    if (typeof value === "string") return value;
    if (value && typeof value === "object") {
      const text = value.diff ?? value.patch ?? value.text ?? value.content;
      if (typeof text === "string") return text;
    }
    return value === null || value === undefined ? "当前没有可显示的差异。" : safeJSON(value);
  }

  async function loadGit(version = state.viewVersion) {
    const session = currentSession();
    if (!session) return;
    if (state.git.sessionId !== session.id) {
      state.git = { sessionId: session.id, status: null, diff: null, snapshots: [], loading: false, errors: [], snapshotBusy: false };
    }
    state.git.loading = true;
    state.git.errors = [];
    if (state.activeTab === "git") renderContext();
    const results = await Promise.allSettled([
      api(sessionURL(session.id, "/git/status")),
      api(sessionURL(session.id, "/git/diff")),
      api(sessionURL(session.id, "/git/snapshots"))
    ]);
    if (version !== state.viewVersion || session.id !== state.currentSessionId) return;
    state.git.loading = false;
    results.forEach((result, index) => {
      const keys = ["status", "diff", "snapshots"];
      const labels = ["Git 状态", "Git 差异", "快照列表"];
      if (result.status === "fulfilled") {
        if (keys[index] === "snapshots") state.git.snapshots = unwrapList(result.value, "snapshots");
        else state.git[keys[index]] = result.value;
      } else {
        state.git.errors.push(labels[index] + "：" + String(result.reason && result.reason.message || result.reason || "请求失败"));
      }
    });
    if (state.activeTab === "git") renderContext();
  }

  function renderGitPanel() {
    const toolbar = node("div", "panel-toolbar");
    const label = node("div", "panel-title");
    label.append(node("span", "panel-icon", "⌘"), node("strong", "", "Git 工作区"));
    const actions = node("div", "git-toolbar-actions");
    const refresh = node("button", "subtle-button", state.git.loading ? "读取中…" : "刷新");
    refresh.type = "button";
    refresh.disabled = state.git.loading;
    refresh.addEventListener("click", () => loadGit(state.viewVersion));
    const snapshot = node("button", "subtle-button", state.git.snapshotBusy ? "创建中…" : "手工快照");
    snapshot.type = "button";
    snapshot.disabled = state.git.snapshotBusy || state.git.loading;
    snapshot.addEventListener("click", createGitSnapshot);
    actions.append(refresh, snapshot);
    toolbar.append(label, actions);
    contextContent.append(toolbar);

    if (state.git.loading && !state.git.status && !state.git.diff) {
      contextContent.append(node("div", "context-empty", "正在读取 Git 状态、差异和快照…"));
    }
    state.git.errors.forEach((message) => contextContent.append(node("div", "git-inline-error", message)));

    const statusCard = node("section", "git-section");
    statusCard.append(node("h3", "git-section-title", "当前状态"));
    if (state.git.status && typeof state.git.status === "object" && !Array.isArray(state.git.status)) {
      const entries = Object.entries(state.git.status);
      if (entries.length) {
        const list = node("dl", "git-status-list");
        entries.forEach(([key, value]) => {
          const row = node("div", "git-status-row");
          row.append(node("dt", "", key.replaceAll("_", " ")), node("dd", "", gitDisplayValue(value)));
          list.append(row);
        });
        statusCard.append(list);
      } else statusCard.append(node("div", "context-empty compact-empty", "Git 状态为空。"));
    } else if (state.git.status !== null) {
      statusCard.append(node("pre", "git-code", gitDisplayValue(state.git.status)));
    } else if (!state.git.loading) {
      statusCard.append(node("div", "context-empty compact-empty", "暂时没有 Git 状态。"));
    }
    contextContent.append(statusCard);

    const diffCard = node("section", "git-section");
    diffCard.append(node("h3", "git-section-title", "工作区差异"));
    if (state.git.diff !== null) {
      diffCard.append(node("pre", "git-code", gitDiffText(state.git.diff)));
    } else if (!state.git.loading) {
      diffCard.append(node("div", "context-empty compact-empty", "暂时没有 Git 差异。"));
    }
    contextContent.append(diffCard);

    const snapshots = node("section", "git-section");
    const snapshotHeading = node("div", "git-snapshot-heading");
    snapshotHeading.append(node("h3", "git-section-title", "手工快照"));
    snapshotHeading.append(node("span", "git-count", String(state.git.snapshots.length)));
    snapshots.append(snapshotHeading);
    if (!state.git.snapshots.length) {
      snapshots.append(node("div", "context-empty compact-empty", state.git.loading ? "正在读取快照…" : "还没有快照。"));
    }
    state.git.snapshots.forEach((item, index) => renderGitSnapshot(item, index, snapshots));
    contextContent.append(snapshots);
  }

  function snapshotId(snapshot) {
    if (typeof snapshot === "string" || typeof snapshot === "number") return String(snapshot);
    if (!snapshot || typeof snapshot !== "object") return "";
    const id = snapshot.id ?? snapshot.snapshot_id ?? snapshot.identifier;
    return id === undefined || id === null ? "" : String(id);
  }

  function snapshotPaths(snapshot) {
    if (!snapshot || typeof snapshot !== "object") return [];
    const list = snapshot.files || snapshot.paths || snapshot.entries || snapshot.manifest;
    if (Array.isArray(list)) {
      return list.map((item) => typeof item === "string" ? item : item && (item.path || item.relative_path || item.name)).filter(Boolean);
    }
    if (list && typeof list === "object") return Object.keys(list);
    return snapshot.path ? [snapshot.path] : [];
  }

  function renderGitSnapshot(snapshot, index, parent) {
    const card = node("article", "git-snapshot");
    const id = snapshotId(snapshot);
    const heading = node("div", "git-snapshot-title");
    const label = snapshot && typeof snapshot === "object"
      ? snapshot.created_at || snapshot.createdAt || snapshot.name || id || "快照 " + (index + 1)
      : id || "快照 " + (index + 1);
    heading.append(node("strong", "", String(label)));
    if (id) heading.append(node("span", "git-snapshot-id", id));
    card.append(heading);
    const paths = snapshotPaths(snapshot);
    if (paths.length) {
      const list = node("div", "git-snapshot-files");
      paths.forEach((path) => {
        const row = node("div", "git-snapshot-file");
        row.append(node("span", "git-snapshot-path", path));
        const preview = node("button", "subtle-button", "预览恢复");
        preview.type = "button";
        preview.disabled = !id;
        preview.addEventListener("click", () => previewGitRestore(id, path, preview));
        row.append(preview);
        list.append(row);
      });
      card.append(list);
    } else {
      const form = document.createElement("form");
      form.className = "git-restore-path-form";
      const input = node("input", "text-input");
      input.placeholder = "输入快照中的相对路径";
      input.setAttribute("aria-label", "快照中的文件相对路径");
      const preview = node("button", "subtle-button", "预览恢复");
      preview.type = "submit";
      preview.disabled = !id;
      form.append(input, preview);
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        const path = input.value.trim();
        if (path) previewGitRestore(id, path, preview);
      });
      card.append(form);
    }
    parent.append(card);
  }

  async function createGitSnapshot() {
    const session = currentSession();
    if (!session || state.git.snapshotBusy) return;
    const viewVersion = state.viewVersion;
    const gitState = state.git;
    gitState.snapshotBusy = true;
    renderContext();
    try {
      await api(sessionURL(session.id, "/git/snapshots"), { method: "POST", body: {} });
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId) return;
      await loadGit(viewVersion);
      notify("已创建手工快照");
    } catch (error) {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) {
        state.git.errors = ["创建手工快照失败：" + error.message];
        if (state.activeTab === "git") renderContext();
      }
    } finally {
      gitState.snapshotBusy = false;
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId && state.activeTab === "git") renderContext();
    }
  }

  async function previewGitRestore(id, path, button) {
    const session = currentSession();
    if (!session || !id || !path) return;
    const viewVersion = state.viewVersion;
    const requestVersion = ++state.gitPreviewRequestVersion;
    if (button) button.disabled = true;
    try {
      const preview = await api(sessionURL(session.id, "/git/restore-preview"), {
        method: "POST",
        body: { snapshot_id: id, path }
      });
      if (session.id !== state.currentSessionId || viewVersion !== state.viewVersion || requestVersion !== state.gitPreviewRequestVersion) return;
      const hasCurrentHash = preview && Object.prototype.hasOwnProperty.call(preview, "current_hash");
      const hasDiff = preview && Object.prototype.hasOwnProperty.call(preview, "diff");
      state.gitPreview = {
        sessionId: session.id,
        snapshotId: id,
        path,
        canRestore: Boolean(hasCurrentHash && hasDiff && preview.can_restore !== false),
        diff: preview && preview.diff
      };
      if (hasCurrentHash) state.gitPreview.expectedHash = preview.current_hash;
      el("gitRestorePreviewMeta").textContent = "文件：" + path + "\n快照：" + id + "\n当前文件哈希：" + (hasCurrentHash ? gitDisplayValue(preview.current_hash) : "预览未返回 current_hash");
      el("gitRestorePreviewDiff").textContent = gitDiffText(preview && preview.diff !== undefined ? preview.diff : preview);
      const error = el("gitRestorePreviewError");
      error.textContent = !hasCurrentHash ? "此预览缺少当前文件哈希，无法安全确认恢复。请刷新后重试。" : !hasDiff ? "此预览没有返回差异，无法安全确认恢复。请刷新后重试。" : "";
      error.hidden = Boolean(hasCurrentHash && hasDiff);
      el("confirmGitRestore").disabled = !state.gitPreview.canRestore;
      el("gitRestoreModal").hidden = false;
    } catch (error) {
      if (session.id === state.currentSessionId && viewVersion === state.viewVersion && requestVersion === state.gitPreviewRequestVersion) {
        reportError("读取恢复预览失败：" + error.message);
      }
    } finally {
      if (button) button.disabled = false;
    }
  }

  function closeGitRestoreModal() {
    state.gitPreviewRequestVersion += 1;
    el("gitRestoreModal").hidden = true;
    state.gitPreview = null;
    el("confirmGitRestore").disabled = false;
    el("confirmGitRestore").textContent = "允许恢复此文件";
    el("gitRestorePreviewError").hidden = true;
    el("gitRestorePreviewError").textContent = "";
  }

  async function confirmGitRestore() {
    const preview = state.gitPreview;
    if (!preview || !preview.canRestore || preview.sessionId !== state.currentSessionId) return;
    const viewVersion = state.viewVersion;
    const button = el("confirmGitRestore");
    button.disabled = true;
    button.textContent = "正在恢复…";
    const errorBox = el("gitRestorePreviewError");
    errorBox.hidden = true;
    try {
      const result = await api(sessionURL(preview.sessionId, "/git/restore"), {
        method: "POST",
        body: {
          snapshot_id: preview.snapshotId,
          path: preview.path,
          expected_hash: preview.expectedHash,
          allow: true
        }
      });
      if (state.gitPreview !== preview || state.viewVersion !== viewVersion || state.currentSessionId !== preview.sessionId) return;
      if (!result.restored) throw new Error(result.message || "恢复未执行，请重新预览文件");
      closeGitRestoreModal();
      await loadGit(viewVersion);
      notify("文件已按预览恢复");
    } catch (error) {
      if (state.gitPreview === preview && state.viewVersion === viewVersion && state.currentSessionId === preview.sessionId) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      }
    } finally {
      if (state.gitPreview === preview) {
        button.disabled = false;
        button.textContent = "允许恢复此文件";
      }
    }
  }

  function renderFilesPanel() {
    const toolbar = node("div", "panel-toolbar");
    const label = node("div", "panel-title");
    label.append(node("span", "panel-icon", "▤"), node("strong", "", "工作区文件"));
    const refresh = node("button", "subtle-button", "刷新");
    refresh.type = "button";
    refresh.addEventListener("click", () => loadFiles(state.viewVersion));
    toolbar.append(label, refresh);
    contextContent.append(toolbar);
    if (state.selectedFile) {
      const back = node("button", "file-back", "← 返回文件列表");
      back.type = "button";
      back.addEventListener("click", () => {
        state.fileRequestVersion += 1;
        state.selectedFile = null;
        renderContext();
      });
      contextContent.append(back);
      contextContent.append(node("div", "file-view-path", state.selectedFile.path));
      contextContent.append(node("pre", "file-content", state.selectedFile.content));
      return;
    }
    if (!state.files.length) {
      contextContent.append(node("div", "context-empty", "此工作区暂时没有可显示的文件。"));
      return;
    }
    const list = node("div", "file-list");
    state.files.forEach((file) => {
      const path = typeof file === "string" ? file : file.path || file.relative_path || file.name || "";
      if (!path) return;
      const button = node("button", "file-row");
      button.type = "button";
      button.append(node("span", "file-type-icon", fileIcon(path)), node("span", "file-name", path), node("span", "file-chevron", "›"));
      button.addEventListener("click", () => loadFile(path));
      list.append(button);
    });
    contextContent.append(list);
  }

  function fileIcon(path) {
    const extension = path.split(".").pop().toLowerCase();
    if (["py", "js", "ts", "jsx", "tsx", "html", "css", "json", "md", "yml", "yaml", "toml"].includes(extension)) return "</>";
    if (["png", "jpg", "jpeg", "svg", "webp"].includes(extension)) return "▧";
    return "▤";
  }

  async function loadFiles(version) {
    const session = currentSession();
    if (!session) return;
    try {
      const data = await api(sessionURL(session.id, "/files"));
      if (version !== state.viewVersion || session.id !== state.currentSessionId) return;
      state.files = Array.isArray(data) ? data : (data && Array.isArray(data.files) ? data.files : []);
      if (state.activeTab === "files") renderContext();
    } catch (error) {
      if (version === state.viewVersion) {
        state.files = [];
        if (state.activeTab === "files") renderContext();
        reportError("读取工作区文件失败：" + error.message);
      }
    }
  }

  async function loadFile(path) {
    const session = currentSession();
    if (!session) return;
    const viewVersion = state.viewVersion;
    const requestVersion = ++state.fileRequestVersion;
    try {
      const data = await api(sessionURL(session.id, "/file") + "?path=" + encodeURIComponent(path));
      if (
        viewVersion !== state.viewVersion ||
        requestVersion !== state.fileRequestVersion ||
        session.id !== state.currentSessionId
      ) return;
      state.selectedFile = { path: data.path || path, content: typeof data.content === "string" ? data.content : safeJSON(data.content) };
      if (state.activeTab === "files") renderContext();
    } catch (error) {
      if (viewVersion === state.viewVersion && requestVersion === state.fileRequestVersion) {
        reportError("读取文件失败：" + error.message);
      }
    }
  }

  function renderSearchPanel() {
    const intro = node("div", "panel-intro");
    intro.append(node("div", "panel-icon large-icon", "⌕"));
    const copy = node("div");
    copy.append(node("strong", "", "混合检索"));
    copy.append(node("p", "", "在当前会话索引中检索相关内容。"));
    intro.append(copy);
    contextContent.append(intro);
    const indexButton = node("button", "secondary-button full-width", "更新知识索引");
    indexButton.type = "button";
    indexButton.id = "indexButton";
    indexButton.addEventListener("click", buildIndex);
    contextContent.append(indexButton);
    if (state.indexSummary) {
      const summary = state.indexSummary;
      contextContent.append(node("p", "panel-intro", "本次更新：" + summary.files + " 个文件、" + summary.chunks +
        " 个块；复用 " + summary.reused_chunks + " 块，重新计算 " + summary.embedded_chunks +
        " 块，移除 " + summary.removed_files + " 个旧文件。"));
    }
    const form = document.createElement("form");
    form.className = "search-form";
    const input = node("input", "text-input");
    input.type = "search";
    input.placeholder = "输入关键词或问题…";
    input.setAttribute("aria-label", "检索知识索引");
    input.value = state.searchQuery;
    input.id = "searchQuery";
    const button = node("button", "primary-button", "检索");
    button.type = "submit";
    form.append(input, button);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await searchIndex(input.value.trim());
    });
    contextContent.append(form);
    if (state.searchResults !== null) {
      if (state.searchResults.loading) {
        contextContent.append(node("div", "search-empty", "正在检索当前索引…"));
        return;
      }
      const results = Array.isArray(state.searchResults) ? state.searchResults : (state.searchResults.results || state.searchResults.items || []);
      if (Array.isArray(results) && results.length) {
        const list = node("div", "search-results");
        results.forEach((result, index) => {
          const card = node("article", "search-result");
          const title = result.title || result.path || result.source || "结果 " + (index + 1);
          card.append(node("div", "result-title", title));
          const content = typeof result === "string" ? result : result.content || result.text || safeJSON(result);
          card.append(node("div", "result-content", content));
          if (result.score !== undefined) card.append(node("div", "result-score", "相关度 " + result.score));
          list.append(card);
        });
        contextContent.append(list);
      } else {
        contextContent.append(node("div", "search-empty", state.searchResults.message || "没有找到相关内容。"));
      }
    }
  }

  async function buildIndex() {
    const session = currentSession();
    if (!session) return;
    const viewVersion = state.viewVersion;
    const button = el("indexButton");
    button.disabled = true;
    button.textContent = "正在更新索引…";
    try {
      const result = await api(sessionURL(session.id, "/index"), { method: "POST" });
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) {
        state.indexSummary = result;
        notify(result && (result.message || result.status) ? String(result.message || result.status) : "知识索引已更新");
        reportError("");
      }
    } catch (error) {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) reportError("更新知识索引失败：" + error.message);
    } finally {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId && state.activeTab === "search") renderContext();
    }
  }

  async function searchIndex(query) {
    const session = currentSession();
    if (!session || !query) return;
    const viewVersion = state.viewVersion;
    const requestVersion = ++state.searchRequestVersion;
    state.searchQuery = query;
    state.searchResults = { loading: true };
    renderContext();
    try {
      const results = await api(sessionURL(session.id, "/search"), {
        method: "POST",
        body: { query }
      });
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId || requestVersion !== state.searchRequestVersion) return;
      state.searchResults = results;
      reportError("");
    } catch (error) {
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId || requestVersion !== state.searchRequestVersion) return;
      state.searchResults = { message: error.message };
      reportError("知识检索失败：" + error.message);
    }
    if (viewVersion === state.viewVersion && session.id === state.currentSessionId &&
        requestVersion === state.searchRequestVersion && state.activeTab === "search") renderContext();
  }

  async function loadMemories(version) {
    const session = currentSession();
    if (!session) return;
    try {
      const data = await api(sessionURL(session.id, "/memories"));
      if (version !== state.viewVersion || session.id !== state.currentSessionId) return;
      state.memories = Array.isArray(data) ? data : (data && Array.isArray(data.memories) ? data.memories : []);
      if (state.activeTab === "memories") renderContext();
    } catch (error) {
      if (version === state.viewVersion) {
        state.memories = [];
        if (state.activeTab === "memories") renderContext();
        reportError("读取长期记忆失败：" + error.message);
      }
    }
  }

  function renderMemoriesPanel() {
    const intro = node("div", "panel-intro");
    intro.append(node("div", "panel-icon large-icon", "✧"));
    const copy = node("div");
    copy.append(node("strong", "", "长期记忆"));
    copy.append(node("p", "", "管理此会话可复用的项目背景与偏好。"));
    intro.append(copy);
    contextContent.append(intro);
    const form = document.createElement("form");
    form.className = "memory-form";
    const input = node("textarea", "text-input memory-input");
    input.placeholder = "添加一条对后续任务有帮助的记忆…";
    input.setAttribute("aria-label", "新的长期记忆");
    input.maxLength = 4000;
    const submit = node("button", "primary-button full-width", "保存记忆");
    submit.type = "submit";
    form.append(input, submit);
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      await addMemory(input.value.trim(), submit);
    });
    contextContent.append(form);
    const list = node("div", "memory-list");
    if (!state.memories.length) list.append(node("div", "context-empty compact-empty", "暂时没有长期记忆。"));
    state.memories.forEach((memory) => {
      const item = node("article", "memory-item");
      const content = typeof memory === "string" ? memory : memory.content || safeJSON(memory);
      const memoryId = memory && typeof memory === "object" ? memory.id : null;
      const hasMemoryId = memoryId !== undefined && memoryId !== null;
      if (hasMemoryId && String(memoryId) === String(state.editingMemoryId)) {
        const editForm = document.createElement("form");
        editForm.className = "memory-edit-form";
        const editor = node("textarea", "text-input memory-input");
        editor.maxLength = 4000;
        editor.value = content;
        editor.setAttribute("aria-label", "编辑长期记忆");
        const editActions = node("div", "memory-edit-actions");
        const save = node("button", "primary-button", "保存修改");
        const cancel = node("button", "secondary-button", "取消");
        save.type = cancel.type = "button";
        save.addEventListener("click", () => updateMemory(memoryId, editor.value.trim(), save));
        cancel.addEventListener("click", () => {
          state.editingMemoryId = null;
          renderContext();
        });
        editActions.append(cancel, save);
        editForm.append(editor, editActions);
        editForm.addEventListener("submit", (event) => {
          event.preventDefault();
          updateMemory(memoryId, editor.value.trim(), save);
        });
        item.append(editForm);
      } else {
        item.append(node("p", "memory-content", content));
      }
      const footer = node("div", "memory-footer");
      const meta = memory.created_at || memory.updated_at || "";
      if (meta) footer.append(node("span", "memory-date", meta));
      const actions = node("div", "memory-actions");
      if (hasMemoryId && String(memoryId) !== String(state.editingMemoryId)) {
        const edit = node("button", "edit-memory", "编辑");
        edit.type = "button";
        edit.addEventListener("click", () => {
          state.editingMemoryId = String(memoryId);
          renderContext();
          const editor = contextContent.querySelector(".memory-edit-form textarea");
          if (editor) editor.focus();
        });
        actions.append(edit);
      }
      if (hasMemoryId) {
        const remove = node("button", "delete-memory", "删除");
        remove.type = "button";
        remove.addEventListener("click", () => deleteMemory(memoryId));
        actions.append(remove);
      }
      footer.append(actions);
      item.append(footer);
      list.append(item);
    });
    contextContent.append(list);
  }

  async function addMemory(content, button) {
    const session = currentSession();
    if (!session || !content) return;
    const viewVersion = state.viewVersion;
    button.disabled = true;
    try {
      await api(sessionURL(session.id, "/memories"), { method: "POST", body: { content } });
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId) return;
      await loadMemories(viewVersion);
      notify("记忆已保存");
    } catch (error) {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) reportError("保存记忆失败：" + error.message);
    } finally {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId && state.activeTab === "memories") renderContext();
    }
  }

  async function deleteMemory(id) {
    if (id === undefined || id === null) {
      reportError("这条记忆没有可用的编号，暂时无法删除。");
      return;
    }
    const session = currentSession();
    if (!session) return;
    const viewVersion = state.viewVersion;
    try {
      await api("/api/memories/" + encodeURIComponent(id), { method: "DELETE" });
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId) return;
      state.memories = state.memories.filter((memory) => String(memory.id) !== String(id));
      if (state.activeTab === "memories") renderContext();
      notify("记忆已删除");
    } catch (error) {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) reportError("删除记忆失败：" + error.message);
    }
  }

  async function updateMemory(id, content, button) {
    if (!content) {
      reportError("记忆内容不能为空。");
      return;
    }
    const session = currentSession();
    if (!session) return;
    const viewVersion = state.viewVersion;
    button.disabled = true;
    try {
      await api("/api/memories/" + encodeURIComponent(id), {
        method: "PATCH",
        body: { content }
      });
      if (viewVersion !== state.viewVersion || session.id !== state.currentSessionId) return;
      state.editingMemoryId = null;
      await loadMemories(viewVersion);
      notify("记忆已更新");
      reportError("");
    } catch (error) {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId) reportError("更新记忆失败：" + error.message);
    } finally {
      if (viewVersion === state.viewVersion && session.id === state.currentSessionId && state.activeTab === "memories") renderContext();
    }
  }

  function openSessionModal() {
    el("createSessionError").hidden = true;
    el("createSessionForm").reset();
    updateWorkspacePresets();
    el("sessionModal").hidden = false;
    window.setTimeout(() => el("newSessionTitle").focus(), 0);
  }

  function closeSessionModal() {
    el("sessionModal").hidden = true;
  }

  async function createSession(event) {
    event.preventDefault();
    const title = el("newSessionTitle").value.trim();
    const workspace = el("workspaceInput").value.trim();
    const absolute = workspace.startsWith("/");
    const error = el("createSessionError");
    if (!absolute) {
      error.textContent = "请输入服务可访问的 Linux 绝对路径，例如 /home/me/project 或 /mnt/c/Users/me/project。";
      error.hidden = false;
      return;
    }
    const submit = el("createSessionSubmit");
    submit.disabled = true;
    error.hidden = true;
    try {
      const created = await api("/api/sessions", { method: "POST", body: { title, workspace } });
      await loadSessions(created && created.id);
      closeSessionModal();
      notify("会话已创建");
    } catch (requestError) {
      error.textContent = requestError.message;
      error.hidden = false;
    } finally {
      submit.disabled = false;
    }
  }

  async function checkHealth() {
    try {
      const health = await api("/api/health");
      const ready = Boolean(health && health.model_ready);
      const provider = health && health.provider ? String(health.provider) : "";
      const model = health && health.model ? String(health.model) : "";
      const badge = el("modelBadge");
      badge.className = "model-badge " + (ready ? "ready" : "not-ready");
      badge.replaceChildren(node("span", "model-dot"), node("span", "", ready ? (provider + (model ? " · " + model : "")) : "模型尚未就绪"));
      if (!ready) {
        const features = health && Array.isArray(health.features) ? health.features : [];
        const detail = features.length ? "可用能力：" + features.join("、") : "请检查服务端模型配置后再启动任务。";
        el("modelWarning").textContent = "模型未配置或尚未就绪。" + (provider || model ? " 当前配置：" + [provider, model].filter(Boolean).join(" · ") + "。" : " ") + detail;
        el("modelWarning").hidden = false;
      } else {
        el("modelWarning").hidden = true;
      }
    } catch (error) {
      el("modelBadge").className = "model-badge not-ready";
      el("modelBadge").replaceChildren(node("span", "model-dot"), node("span", "", "无法读取模型状态"));
      reportError("读取服务状态失败：" + error.message);
    }
  }

  function openMobileSidebar() {
    el("sidebar").classList.add("mobile-open");
    el("sidebarScrim").classList.add("visible");
  }

  function closeMobileSidebar() {
    el("sidebar").classList.remove("mobile-open");
    el("sidebarScrim").classList.remove("visible");
  }

  function wireUI() {
    el("newSessionButton").addEventListener("click", openSessionModal);
    el("closeSessionModal").addEventListener("click", closeSessionModal);
    el("cancelSessionCreate").addEventListener("click", closeSessionModal);
    el("createSessionForm").addEventListener("submit", createSession);
    el("workspacePreset").addEventListener("change", (event) => {
      if (event.target.value) el("workspaceInput").value = event.target.value;
      else el("workspaceInput").focus();
    });
    el("sidebarToggle").addEventListener("click", openMobileSidebar);
    el("sidebarScrim").addEventListener("click", closeMobileSidebar);
    el("refreshButton").addEventListener("click", async () => {
      reportError("");
      try {
        await checkHealth();
        await loadSessions(state.currentSessionId);
        notify("工作台已刷新");
      } catch (error) {
        reportError("刷新失败：" + error.message);
      }
    });
    document.querySelectorAll(".context-tab").forEach((tab) => {
      tab.addEventListener("click", () => {
        const previousTab = state.activeTab;
        state.activeTab = tab.dataset.tab;
        if (previousTab === "tasks" && state.activeTab !== "tasks") stopTaskPolling();
        renderContext();
        if (state.activeTab === "git") loadGit(state.viewVersion);
        if (state.activeTab === "tasks") {
          startTaskPolling();
          refreshTasks(state.viewVersion);
        }
      });
    });
    el("closeGitRestoreModal").addEventListener("click", closeGitRestoreModal);
    el("cancelGitRestore").addEventListener("click", closeGitRestoreModal);
    el("confirmGitRestore").addEventListener("click", confirmGitRestore);
    el("gitRestoreModal").addEventListener("click", (event) => {
      if (event.target === el("gitRestoreModal")) closeGitRestoreModal();
    });
    document.querySelectorAll(".suggestion-chip").forEach((button) => {
      button.addEventListener("click", () => {
        if (!currentSession()) {
          openSessionModal();
          return;
        }
        messageInput.value = button.dataset.prompt || "";
        saveSessionDraft(state.currentSessionId, messageInput.value);
        messageInput.focus();
        resizeComposer();
      });
    });
    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const value = messageInput.value;
      if (!value.trim() || state.busy) return;
      submitMessage(value);
    });
    messageInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey && !event.isComposing && event.keyCode !== 229) {
        event.preventDefault();
        chatForm.requestSubmit();
      }
    });
    messageInput.addEventListener("input", () => {
      resizeComposer();
      saveSessionDraft(state.currentSessionId, messageInput.value);
    });
    sessionSearchInput.addEventListener("input", renderSessions);
    el("sessionModal").addEventListener("click", (event) => {
      if (event.target === el("sessionModal")) closeSessionModal();
    });
    document.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        sessionSearchInput.focus();
        sessionSearchInput.select();
      }
      if (event.key === "Escape" && !el("sessionModal").hidden) closeSessionModal();
      if (event.key === "Escape" && !el("gitRestoreModal").hidden) closeGitRestoreModal();
      if (event.key === "Escape" && sessionSearchInput.value) {
        event.preventDefault();
        sessionSearchInput.value = "";
        renderSessions();
      }
    });
  }

  function resizeComposer() {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + "px";
  }

  async function initialize() {
    wireUI();
    setAPIStatus("连接服务中", "connecting");
    setStreamStatus("等待任务", "");
    try {
      await checkHealth();
      await loadSessions();
      if (!state.currentSessionId) setAPIStatus("服务已连接", "online");
    } catch (error) {
      setAPIStatus("服务连接失败", "offline");
      reportError("无法载入工作台：" + error.message);
    }
  }

  initialize();
})();
