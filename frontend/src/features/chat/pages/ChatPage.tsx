import { useEffect, useRef, useState } from "react";
import {
  Archive,
  Bot,
  Check,
  ChevronDown,
  Clipboard,
  FileText,
  MessageSquare,
  MoreHorizontal,
  Paperclip,
  Plus,
  RotateCcw,
  Search,
  Send,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  Workflow,
} from "lucide-react";

import styles from "./ChatPage.module.css";

type ChatRole = "user" | "assistant";

type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  timestamp: string;
  citations?: string[];
  metrics?: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: "message-1",
    role: "user",
    content: "请帮我梳理这份招标文件的技术响应重点，并指出需要补充的证明材料。",
    timestamp: "今天 10:42",
  },
  {
    id: "message-2",
    role: "assistant",
    content:
      "我已经基于当前选中的知识库完成初步梳理。技术响应可以优先关注三个方面：\n\n1. 项目实施方案是否覆盖招标文件中的交付边界与验收节点。\n2. 关键技术指标是否逐项给出响应值、测试方法和佐证材料。\n3. 团队与服务保障部分是否提供项目负责人、类似业绩和售后响应承诺。\n\n建议补充：产品检测报告、近三年类似项目合同关键页，以及项目团队成员的资质证书。",
    timestamp: "今天 10:42",
    citations: ["招标文件 · 技术需求 · 第 18 页", "企业资质库 · 业绩证明 · 2024 年版"],
    metrics: "检索 6 个片段 · 1.8s · 612 tokens",
  },
];

const conversationItems = [
  { id: "tender-response", title: "投标文件技术响应梳理", meta: "今天 10:42", active: true },
  { id: "qualification", title: "企业资质材料清单", meta: "昨天 16:20" },
  { id: "delivery-plan", title: "项目交付计划初稿", meta: "2026/07/22" },
  { id: "retrieval-test", title: "知识库检索效果测试", meta: "2026/07/21" },
];

const promptSuggestions = [
  "总结这份招标文件",
  "生成技术响应目录",
  "查找类似项目业绩",
];

export function ChatPage() {
  const [activeConversation, setActiveConversation] = useState("tender-response");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [inputValue, setInputValue] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(true);
  const messageStreamRef = useRef<HTMLDivElement>(null);
  const responseTimerRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    const stream = messageStreamRef.current;
    if (stream) stream.scrollTo({ top: stream.scrollHeight, behavior: "smooth" });
  }, [messages, isThinking]);

  useEffect(() => () => {
    if (responseTimerRef.current) window.clearTimeout(responseTimerRef.current);
  }, []);

  const handleNewConversation = () => {
    setActiveConversation("new-conversation");
    setMessages([]);
    setInputValue("");
    setIsThinking(false);
  };

  const handleConversationSelect = (conversationId: string) => {
    setActiveConversation(conversationId);
    setMessages(conversationId === "tender-response" ? initialMessages : []);
    setInputValue("");
    setIsThinking(false);
  };

  const handleSend = (suggestion?: string) => {
    const content = (suggestion ?? inputValue).trim();
    if (!content || isThinking) return;

    const now = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
    setMessages((current) => [
      ...current,
      { id: `user-${Date.now()}`, role: "user", content, timestamp: `今天 ${now}` },
    ]);
    setInputValue("");
    setIsThinking(true);
    responseTimerRef.current = window.setTimeout(() => {
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${Date.now()}`,
          role: "assistant",
          content: `已完成对“${content}”的 mock 分析。后续接入 LangChain 时，这里可以替换为真实的检索、工具调用和流式响应结果。`,
          timestamp: `今天 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`,
          citations: useKnowledgeBase ? ["招标文件 · 已选知识库 · 相关片段"] : undefined,
          metrics: "Mock 响应 · 0.6s · 128 tokens",
        },
      ]);
      setIsThinking(false);
    }, 900);
  };

  const handleCopy = async (content: string) => {
    await navigator.clipboard?.writeText(content);
  };

  return (
    <div className={styles.page}>
      <aside className={styles.conversationList} aria-label="历史会话">
        <div className={styles.listHeading}>
          <div>
            <span className={styles.eyebrow}>CONVERSATIONS</span>
            <h1>对话</h1>
          </div>
          <button className={styles.iconButton} type="button" title="更多会话操作" aria-label="更多会话操作">
            <MoreHorizontal size={17} />
          </button>
        </div>

        <button className={styles.newConversationButton} type="button" onClick={handleNewConversation}>
          <Plus size={16} />
          新建对话
        </button>

        <label className={styles.conversationSearch}>
          <Search size={14} />
          <input aria-label="搜索会话" placeholder="搜索会话" />
        </label>

        <div className={styles.listSectionLabel}>最近对话</div>
        <div className={styles.conversationItems}>
          {conversationItems.map((conversation) => (
            <button
              className={`${styles.conversationItem} ${activeConversation === conversation.id ? styles.conversationItemActive : ""}`}
              key={conversation.id}
              type="button"
              onClick={() => handleConversationSelect(conversation.id)}
            >
              <MessageSquare size={15} />
              <span className={styles.conversationCopy}>
                <strong>{conversation.title}</strong>
                <small>{conversation.meta}</small>
              </span>
            </button>
          ))}
        </div>

        <div className={styles.storageHint}>
          <Archive size={14} />
          <span><strong>4</strong> 个会话 · 已自动保存</span>
        </div>
      </aside>

      <section className={styles.chatWorkspace}>
        <header className={styles.chatHeader}>
          <div className={styles.agentIdentity}>
            <div className={styles.agentIcon}><Bot size={19} /></div>
            <div>
              <div className={styles.agentTitle}>投标助手 <span className={styles.statusDot} /> 在线</div>
              <div className={styles.agentSubtitle}>Tender Agent · 检索增强对话</div>
            </div>
          </div>
          <div className={styles.chatHeaderActions}>
            <button className={styles.secondaryButton} type="button" onClick={() => setMessages([])}><RotateCcw size={14} /> 清空上下文</button>
            <button className={styles.iconButton} type="button" title="对话设置" aria-label="对话设置"><MoreHorizontal size={17} /></button>
          </div>
        </header>

        <div className={styles.messageStream} ref={messageStreamRef}>
          {messages.length === 0 && (
            <div className={styles.emptyConversation}>
              <div className={styles.emptyIcon}><Sparkles size={20} /></div>
              <h2>开始一段新的工作对话</h2>
              <p>从招标文件、知识库检索或技术响应开始，投标助手会在这里协助你。</p>
            </div>
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} onCopy={handleCopy} onRetry={() => handleSend(message.content)} />
          ))}
          {isThinking && (
            <div className={styles.assistantRow}>
              <div className={styles.messageAvatar}><Bot size={16} /></div>
              <div className={styles.thinkingBubble}><span /><span /><span /><em>正在检索知识库并组织回答</em></div>
            </div>
          )}
        </div>

        <footer className={styles.composerArea}>
          <div className={styles.suggestionRow}>
            {promptSuggestions.map((suggestion) => (
              <button key={suggestion} type="button" onClick={() => handleSend(suggestion)}>
                <Sparkles size={13} /> {suggestion}
              </button>
            ))}
          </div>
          <div className={styles.composer}>
            <textarea
              aria-label="发送消息"
              value={inputValue}
              onChange={(event) => setInputValue(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              placeholder="输入你想了解的内容..."
              rows={2}
            />
            <div className={styles.composerToolbar}>
              <div className={styles.composerTools}>
                <button type="button" title="添加附件" aria-label="添加附件"><Paperclip size={16} /></button>
                <button type="button" title="添加工作流" aria-label="添加工作流"><Workflow size={16} /></button>
                <span className={styles.composerHint}>Enter 发送 · Shift + Enter 换行</span>
              </div>
              <button className={styles.sendButton} type="button" title="发送消息" aria-label="发送消息" onClick={() => handleSend()} disabled={isThinking || !inputValue.trim()}>
                <Send size={16} />
              </button>
            </div>
          </div>
        </footer>
      </section>

      <aside className={styles.inspector} aria-label="对话上下文">
        <div className={styles.inspectorHeading}>
          <div><span className={styles.eyebrow}>WORKSPACE</span><h2>对话上下文</h2></div>
          <button className={styles.iconButton} type="button" title="收起上下文" aria-label="收起上下文"><ChevronDown size={16} /></button>
        </div>

        <div className={styles.inspectorSection}>
          <div className={styles.sectionTitle}><span>知识库</span><button type="button" className={styles.textButton}>管理</button></div>
          <button className={styles.sourceCard} type="button" onClick={() => setUseKnowledgeBase((value) => !value)}>
            <div className={styles.sourceIcon}><FileText size={16} /></div>
            <div className={styles.sourceCopy}><strong>投标文件知识库</strong><small>128 份文档 · 已发布</small></div>
            <span className={`${styles.toggle} ${useKnowledgeBase ? styles.toggleOn : ""}`}><span /></span>
          </button>
          <div className={styles.contextNote}>{useKnowledgeBase ? "回答会优先引用已发布文档" : "当前回答不使用知识库"}</div>
        </div>

        <div className={styles.inspectorSection}>
          <div className={styles.sectionTitle}><span>当前模型</span><button type="button" className={styles.textButton}>切换</button></div>
          <div className={styles.modelCard}>
            <div className={styles.modelMark}>GLM</div>
            <div className={styles.sourceCopy}><strong>GLM-4-Plus</strong><small>后端适配 · 流式输出</small></div>
            <Check size={15} color="#2aa77c" />
          </div>
        </div>

        <div className={styles.inspectorSection}>
          <div className={styles.sectionTitle}><span>响应设置</span></div>
          <div className={styles.parameterRow}><span>温度</span><strong>0.2</strong></div>
          <div className={styles.parameterTrack}><span style={{ width: "20%" }} /></div>
          <div className={styles.parameterRow}><span>召回数量</span><strong>5</strong></div>
          <div className={styles.parameterRow}><span>引用来源</span><strong>开启</strong></div>
        </div>

        <div className={styles.langchainNote}>
          <div className={styles.langchainIcon}><Workflow size={15} /></div>
          <div><strong>LangChain 测试基底</strong><p>前端仅展示运行上下文，编排逻辑由后端接管。</p></div>
        </div>
      </aside>
    </div>
  );
}

function MessageBubble({ message, onCopy, onRetry }: { message: ChatMessage; onCopy: (content: string) => void; onRetry: () => void }) {
  if (message.role === "user") {
    return <div className={styles.userMessageRow}><div className={styles.userMessage}><p>{message.content}</p><small>{message.timestamp}</small></div></div>;
  }

  return (
    <div className={styles.assistantRow}>
      <div className={styles.messageAvatar}><Bot size={16} /></div>
      <div className={styles.assistantMessageGroup}>
        <div className={styles.assistantMessage}>
          <div className={styles.assistantLabel}>投标助手 <span>已完成</span></div>
          <p>{message.content}</p>
          {message.citations && <div className={styles.citations}>{message.citations.map((citation) => <button key={citation} type="button"><FileText size={13} />{citation}</button>)}</div>}
        </div>
        <div className={styles.messageActions}>
          <button type="button" title="复制回答" aria-label="复制回答" onClick={() => onCopy(message.content)}><Clipboard size={13} /></button>
          <button type="button" title="回答有帮助" aria-label="回答有帮助"><ThumbsUp size={13} /></button>
          <button type="button" title="回答没有帮助" aria-label="回答没有帮助"><ThumbsDown size={13} /></button>
          <button type="button" title="重新生成" aria-label="重新生成" onClick={onRetry}><RotateCcw size={13} /></button>
          {message.metrics && <span>{message.metrics}</span>}
        </div>
      </div>
    </div>
  );
}
