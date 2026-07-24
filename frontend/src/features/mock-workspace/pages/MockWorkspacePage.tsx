import { useState } from "react";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Bot,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CloudUpload,
  Code2,
  Download,
  FileCheck2,
  FileClock,
  FileText,
  FolderOpen,
  GitBranch,
  Layers3,
  ListChecks,
  MessageSquare,
  MoreHorizontal,
  Play,
  Plus,
  RefreshCcw,
  Search,
  Settings2,
  ShieldCheck,
  Sparkles,
  Upload,
  Workflow,
  X,
  Zap,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import styles from "./MockWorkspacePage.module.css";

export type MockPageKind =
  | "dashboard"
  | "agents"
  | "tender"
  | "task"
  | "skeleton"
  | "workflow"
  | "docs"
  | "settings";

type Notice = { tone: "success" | "info"; text: string } | null;

const agentCards = [
  { name: "Tender Agent", key: "tender", description: "把招标文件转换为可执行的投标书章节骨架。", status: "运行中", tone: "green", icon: FileCheck2 },
  { name: "制度检索助手", key: "policy", description: "从已发布制度知识库中检索可追溯的企业事实。", status: "运行中", tone: "green", icon: Search },
  { name: "合同审查员", key: "contract", description: "识别合同中的风险条款并整理审核关注点。", status: "待配置", tone: "amber", icon: ShieldCheck },
];

const recentTasks = [
  { id: "TDR-20260724-001", agent: "Tender Agent", title: "华东区域运维服务项目", status: "已完成", tone: "green", time: "今天 09:34", duration: "2m 18s" },
  { id: "TDR-20260723-004", agent: "制度检索助手", title: "申请材料证明文件检索", status: "已完成", tone: "green", time: "昨天 16:20", duration: "1.8s" },
  { id: "TDR-20260723-002", agent: "Tender Agent", title: "智慧园区建设项目", status: "处理中", tone: "blue", time: "昨天 14:06", duration: "进行中" },
  { id: "TDR-20260722-008", agent: "合同审查员", title: "供应商服务协议初审", status: "待配置", tone: "amber", time: "2026/07/22", duration: "-" },
];

const skeletonSections = [
  { title: "一、项目理解与总体实施方案", required: true, children: ["1.1 项目背景与目标", "1.2 总体实施思路", "1.3 项目范围与边界"] },
  { title: "二、技术方案", required: true, children: ["2.1 总体技术架构", "2.2 关键技术指标响应", "2.3 安全与质量保障"] },
  { title: "三、项目组织与人员配置", required: true, children: ["3.1 项目组织架构", "3.2 核心人员配置", "3.3 人员资质证明"] },
  { title: "四、实施计划与交付物", required: false, children: ["4.1 项目进度计划", "4.2 验收与交付标准"] },
  { title: "五、售后服务与保障", required: false, children: ["5.1 服务响应承诺", "5.2 培训与运维方案"] },
];

export function MockWorkspacePage({ kind }: { kind: MockPageKind }) {
  switch (kind) {
    case "dashboard": return <DashboardMockPage />;
    case "agents": return <AgentsMockPage />;
    case "tender": return <TenderMockPage />;
    case "task": return <TenderTaskMockPage />;
    case "skeleton": return <SkeletonMockPage />;
    case "workflow": return <WorkflowMockPage />;
    case "docs": return <DocsMockPage />;
    case "settings": return <SettingsMockPage />;
  }
}

function DashboardMockPage() {
  const navigate = useNavigate();
  const [range, setRange] = useState("过去 7 天");
  const [notice, setNotice] = useState<Notice>(null);
  const chartValues = [58, 76, 47, 89, 71, 82, 96];

  return <PageShell
    eyebrow="WORKSPACE OVERVIEW"
    title="控制台"
    description="查看智能体、任务和知识资产的整体运行状态。"
    actions={<><button className={styles.buttonSecondary} type="button" onClick={() => setRange(range === "过去 7 天" ? "过去 30 天" : "过去 7 天")}><Clock3 size={14} />{range}</button><button className={styles.buttonSecondary} type="button" onClick={() => setNotice({ tone: "info", text: "Mock 报告已准备好，真实下载接口待接入。" })}><Download size={14} />导出报告</button></>}
    notice={notice}
  >
    <div className={styles.statsGrid}>
      <StatCard icon={Bot} tone="blue" label="活跃智能体" value="24 / 30" note="较上周 +12%" />
      <StatCard icon={ListChecks} tone="green" label="已完成任务" value="128,402" note="今日新增 1,240" />
      <StatCard icon={Activity} tone="purple" label="平均响应时间" value="342 ms" note="全平台平均 410 ms" />
      <StatCard icon={ShieldCheck} tone="amber" label="任务成功率" value="99.98%" note="服务运行稳定" />
    </div>

    <div className={styles.dashboardGrid}>
      <Panel className={styles.chartPanel} title={`任务执行趋势 · ${range}`} action={<span className={styles.legend}><i className={styles.legendSuccess} />成功 <i className={styles.legendRunning} />执行中</span>}>
        <div className={styles.chart}>
          {chartValues.map((height, index) => <div className={styles.chartColumn} key={index}><div className={styles.chartBarTrack}><span style={{ height: `${height}%` }} /></div><small>{index === chartValues.length - 1 ? "今日" : `07/${18 + index}`}</small></div>)}
        </div>
      </Panel>
      <Panel className={styles.insightPanel} title="AI 智能洞察" icon={<Sparkles size={16} />}>
        <div className={styles.insightItem}><span className={styles.insightLabelPurple}>优化建议</span><p>检测到 Tender Agent 在文件解析阶段存在重复重试，建议将大文件拆分后再提交。</p></div>
        <div className={styles.insightItem}><span className={styles.insightLabelGreen}>资源状态</span><p>制度知识库当前已发布 128 份文档，索引服务运行稳定。</p></div>
        <button className={styles.textAction} type="button" onClick={() => navigate("/knowledge-bases/policy/search")}>查看知识检索 <ArrowRight size={13} /></button>
      </Panel>
    </div>

    <Panel title="最近任务动态" action={<button className={styles.textAction} type="button" onClick={() => navigate("/agents")}>查看全部 <ArrowRight size={13} /></button>}>
      <TaskTable onOpen={(task) => navigate(task.agent === "Tender Agent" ? `/agents/tender/tasks/${task.id}` : "/chat")} />
    </Panel>

    <div className={styles.quickStartGrid}>
      <QuickStartCard icon={FileCheck2} title="创建 Tender 任务" description="上传招标文件，生成章节骨架。" onClick={() => navigate("/agents/tender")} />
      <QuickStartCard icon={Search} title="检索知识库" description="从制度文档中快速找到依据。" onClick={() => navigate("/knowledge-bases/policy/search")} />
      <QuickStartCard icon={MessageSquare} title="开始智能对话" description="与投标助手讨论下一步工作。" onClick={() => navigate("/chat")} />
    </div>
  </PageShell>;
}

function AgentsMockPage() {
  const navigate = useNavigate();
  const [notice, setNotice] = useState<Notice>(null);
  return <PageShell eyebrow="AGENT WORKSPACE" title="智能体" description="管理可用的业务智能体，查看运行状态和最近任务。" actions={<button className={styles.buttonPrimary} type="button" onClick={() => setNotice({ tone: "info", text: "创建智能体表单将在后续版本接入。当前先使用 Tender Agent mock。" })}><Plus size={15} />创建智能体</button>} notice={notice}>
    <section className={styles.agentHero}>
      <div className={styles.agentHeroCopy}><div className={styles.heroKicker}>RECOMMENDED AGENT <span>·</span> PHASE 3</div><h2>Tender Agent</h2><p>从招标文件开始，生成可审阅的投标书章节骨架，为后续人工编写保留清晰的结构入口。</p><div className={styles.heroActions}><button className={styles.buttonPrimary} type="button" onClick={() => navigate("/agents/tender")}><Play size={14} />开始一次任务</button><button className={styles.buttonGhost} type="button" onClick={() => navigate("/agents/tender/tasks/TDR-20260724-001/skeleton")}><FileText size={14} />查看示例结果</button></div></div><div className={styles.agentHeroVisual}><div className={styles.heroOrbit} /><div className={styles.heroCore}><FileCheck2 size={26} /></div><span className={`${styles.heroPill} ${styles.heroPillOne}`}>解析</span><span className={`${styles.heroPill} ${styles.heroPillTwo}`}>骨架</span><span className={`${styles.heroPill} ${styles.heroPillThree}`}>审阅</span></div>
    </section>
    <div className={styles.sectionHeading}><div><span className={styles.sectionEyebrow}>AVAILABLE AGENTS</span><h2>可用智能体</h2></div><span className={styles.mutedText}>3 个配置</span></div>
    <div className={styles.agentGrid}>{agentCards.map((agent) => <AgentCard key={agent.key} agent={agent} onOpen={() => agent.key === "tender" ? navigate("/agents/tender") : setNotice({ tone: "info", text: `${agent.name} 当前仅展示 UI mock。` })} />)}</div>
    <Panel title="最近任务" action={<button className={styles.textAction} type="button" onClick={() => navigate("/agents/tender/tasks/TDR-20260724-001")}>查看详情 <ArrowRight size={13} /></button>}><TaskTable onOpen={(task) => navigate(task.agent === "Tender Agent" ? `/agents/tender/tasks/${task.id}` : "/chat")} /></Panel>
  </PageShell>;
}

function TenderMockPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [notice, setNotice] = useState<Notice>(null);
  const mockTaskId = "TDR-20260724-NEW";
  return <PageShell eyebrow="AGENTS / TENDER" title="Tender Agent" description="上传招标文件，创建一次可追踪的投标书骨架任务。" actions={<button className={styles.buttonSecondary} type="button" onClick={() => navigate("/agents") }><ArrowLeft size={14} />返回智能体</button>} notice={notice}>
    <div className={styles.twoColumnGrid}>
      <div className={styles.stack}>
        <Panel title="输入文件" icon={<CloudUpload size={16} />}><label className={styles.dropzone}><input type="file" accept=".pdf,.doc,.docx" onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)} /><CloudUpload size={28} /><strong>{selectedFile ? selectedFile.name : "点击选择招标文件"}</strong><span>{selectedFile ? `${(selectedFile.size / 1024 / 1024).toFixed(1)} MB · 已加入任务` : "支持 PDF、DOC、DOCX，单文件不超过 50 MB"}</span><em>浏览文件</em></label>{selectedFile && <div className={styles.fileRow}><div className={styles.fileIcon}><FileText size={16} /></div><div><strong>{selectedFile.name}</strong><small>待提交 · 原始文件</small></div><button type="button" className={styles.iconButton} title="移除文件" onClick={() => setSelectedFile(null)}><X size={15} /></button></div>}<div className={styles.noteBox}><AlertCircle size={15} /><span>当前 mock 只展示文件输入和任务创建流程，不会上传到后端。</span></div></Panel>
        <Panel title="任务准备检查" icon={<ListChecks size={16} />}><Checklist items={["已选择招标文件", "将生成章节骨架", "任务状态可在详情页追踪"]} /></Panel>
      </div>
      <Panel title="创建任务" icon={<Zap size={16} />}><div className={styles.formStack}><label>任务名称<input defaultValue="华东区域运维服务项目 · 投标书骨架" /></label><label>输出模式<select defaultValue="skeleton"><option value="skeleton">投标书章节骨架</option><option value="outline">技术响应目录</option></select></label><label>备注<textarea defaultValue="请重点关注技术指标响应、项目实施计划和人员资质证明。" rows={5} /></label><div className={styles.formDivider} /><div className={styles.formSummary}><span>预计处理时间</span><strong>约 2 - 5 分钟</strong></div><button className={styles.buttonPrimaryWide} type="button" disabled={!selectedFile} onClick={() => navigate(`/agents/tender/tasks/${mockTaskId}`)}><Play size={15} />创建 Tender 任务</button>{!selectedFile && <small className={styles.formHint}>请先选择一个招标文件</small>}</div></Panel>
    </div>
    <Panel title="最近 Tender 任务" action={<button className={styles.textAction} type="button" onClick={() => navigate(`/agents/tender/tasks/${mockTaskId}`)}>打开示例任务 <ArrowRight size={13} /></button>}><TaskTable tenderOnly onOpen={(task) => navigate(`/agents/tender/tasks/${task.id}`)} /></Panel>
  </PageShell>;
}

function TenderTaskMockPage() {
  const navigate = useNavigate();
  const { taskId = "TDR-20260724-001" } = useParams();
  const [notice, setNotice] = useState<Notice>(null);
  return <PageShell eyebrow="AGENTS / TENDER / TASK" title="任务详情" description={`${taskId} · 华东区域运维服务项目`} actions={<><button className={styles.buttonSecondary} type="button" onClick={() => navigate("/agents/tender")}><ArrowLeft size={14} />返回 Tender Agent</button><button className={styles.buttonSecondary} type="button" onClick={() => setNotice({ tone: "info", text: "Mock 任务已重新排队，真实轮询接口待接入。" })}><RefreshCcw size={14} />重新执行</button></>} notice={notice}>
    <div className={styles.taskMetaRow}><StatusPill label="已完成" tone="green" /><span>创建于今天 09:31</span><span>最后更新 今天 09:34</span><span className={styles.metaId}>任务 ID：{taskId}</span></div>
    <Panel title="处理进度" icon={<Activity size={16} />}><div className={styles.progressHeader}><div><strong>已生成投标书章节骨架</strong><p>任务已完成，等待人工审阅结果结构。</p></div><strong className={styles.progressValue}>100%</strong></div><div className={styles.progressTrack}><span style={{ width: "100%" }} /></div><div className={styles.stageRow}>{["文件接收", "内容解析", "结构生成", "结果整理"].map((stage) => <div className={styles.stageDone} key={stage}><CheckCircle2 size={15} />{stage}</div>)}</div></Panel>
    <div className={styles.twoColumnGrid}><Panel title="任务输入" icon={<FileText size={16} />}><div className={styles.detailList}><DetailRow label="源文件" value="华东区域运维服务项目.pdf" /><DetailRow label="文件大小" value="18.6 MB" /><DetailRow label="处理模式" value="章节骨架生成" /><DetailRow label="执行耗时" value="2m 18s" /></div></Panel><Panel title="结果摘要" icon={<FileCheck2 size={16} />}><div className={styles.resultSummary}><div className={styles.resultNumber}>18</div><div><strong>个章节节点</strong><p>包含 11 个必填章节、7 个补充章节，以及 24 个待填写占位符。</p></div></div><div className={styles.resultActions}><button className={styles.buttonPrimary} type="button" onClick={() => navigate(`/agents/tender/tasks/${taskId}/skeleton`)}><FileText size={14} />预览章节骨架</button><button className={styles.buttonSecondary} type="button" onClick={() => setNotice({ tone: "info", text: "Mock 文件已准备好，真实下载接口待接入。" })}><Download size={14} />下载骨架</button></div></Panel></div>
    <Panel title="任务事件" icon={<Clock3 size={16} />}><div className={styles.timeline}><TimelineItem time="09:34" title="结果已生成" detail="章节骨架和占位符已整理完成。" done /><TimelineItem time="09:33" title="结构生成完成" detail="识别到 5 个一级章节和 18 个章节节点。" done /><TimelineItem time="09:32" title="招标文件解析完成" detail="解析 86 页文档，提取技术要求和商务条款。" done /><TimelineItem time="09:31" title="任务已创建" detail="等待处理流程启动。" done /></div></Panel>
  </PageShell>;
}

function SkeletonMockPage() {
  const navigate = useNavigate();
  const { taskId = "TDR-20260724-001" } = useParams();
  const [notice, setNotice] = useState<Notice>(null);
  return <PageShell eyebrow="AGENTS / TENDER / SKELETON" title="投标书骨架预览" description={`${taskId} · 结构信息与待填写区域`} actions={<><button className={styles.buttonSecondary} type="button" onClick={() => navigate(`/agents/tender/tasks/${taskId}`)}><ArrowLeft size={14} />返回任务详情</button><button className={styles.buttonPrimary} type="button" onClick={() => setNotice({ tone: "info", text: "Mock 骨架文件已准备好，真实下载接口待接入。" })}><Download size={14} />下载骨架</button></>} notice={notice}>
    <div className={styles.skeletonSummary}><div><span className={styles.sectionEyebrow}>STRUCTURE ONLY</span><h2>华东区域运维服务项目 · 投标书章节结构</h2><p>以下内容只展示章节顺序、必填状态和占位位置，不代表已生成正式投标书正文。</p></div><div className={styles.summaryStats}><strong>18</strong><span>章节节点</span><strong>24</strong><span>待填写项</span></div></div>
    <div className={styles.twoColumnGrid}><Panel title="章节树" icon={<Layers3 size={16} />}><div className={styles.skeletonTree}>{skeletonSections.map((section, index) => <div className={styles.treeSection} key={section.title}><div className={styles.treeRow}><ChevronRight size={14} /><span className={styles.treeIndex}>0{index + 1}</span><strong>{section.title}</strong>{section.required ? <Tag label="必填" tone="blue" /> : <Tag label="补充" tone="gray" />}</div><div className={styles.treeChildren}>{section.children.map((child, childIndex) => <div className={styles.treeChild} key={child}><span>{index + 1}.{childIndex + 1}</span>{child}<small>待填写</small></div>)}</div></div>)}</div></Panel><div className={styles.stack}><Panel title="待填写占位符" icon={<AlertCircle size={16} />}><div className={styles.placeholderList}><Placeholder label="项目负责人及核心团队资质" type="人员证明" /><Placeholder label="近三年类似项目合同关键页" type="业绩证明" /><Placeholder label="技术指标逐项响应值" type="技术响应" /><Placeholder label="售后服务响应承诺" type="服务承诺" /></div></Panel><Panel title="结果留痕" icon={<FileText size={16} />}><div className={styles.detailList}><DetailRow label="源文件" value="华东区域运维服务项目.pdf" /><DetailRow label="生成时间" value="2026/07/24 09:34" /><DetailRow label="结构版本" value="Skeleton v0.1" /></div></Panel></div></div>
  </PageShell>;
}

function WorkflowMockPage() {
  const [selected, setSelected] = useState("retrieve");
  const [running, setRunning] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const nodes = [{ id: "input", title: "招标文件输入", detail: "PDF / DOCX", icon: FolderOpen, tone: "blue" }, { id: "parse", title: "文档解析", detail: "结构化提取", icon: Code2, tone: "purple" }, { id: "retrieve", title: "知识检索", detail: "制度知识库", icon: Search, tone: "green" }, { id: "output", title: "结果整理", detail: "章节骨架", icon: FileCheck2, tone: "amber" }];
  return <PageShell eyebrow="WORKFLOW PREVIEW" title="工作流" description="查看 Agent 能力的执行链路和节点配置。当前为 UI mock，暂不连接真实编排引擎。" actions={<><button className={styles.buttonSecondary} type="button" onClick={() => setNotice({ tone: "info", text: "工作流已保存为 mock 草稿。" })}><Check size={14} />保存草稿</button><button className={styles.buttonPrimary} type="button" onClick={() => { setRunning(true); setNotice({ tone: "success", text: "Mock 工作流已开始运行。" }); window.setTimeout(() => setRunning(false), 1200); }}><Play size={14} />{running ? "运行中" : "运行预览"}</button></>} notice={notice}>
    <div className={styles.workflowToolbar}><div className={styles.workflowBreadcrumb}><Workflow size={16} />Tender Agent · 默认处理链路 <span>草稿</span></div><div className={styles.toolbarTools}><button type="button" title="添加节点" onClick={() => setNotice({ tone: "info", text: "节点面板已预留，当前为静态 mock。" })}><Plus size={15} /></button><button type="button" title="工作流设置"><Settings2 size={15} /></button><button type="button" title="更多操作"><MoreHorizontal size={15} /></button></div></div>
     <div className={styles.workflowLayout}><div className={styles.workflowCanvas}><div className={styles.canvasGrid} />{nodes.map((node, index) => <div className={`${styles.workflowNode} ${selected === node.id ? styles.workflowNodeSelected : ""}`} style={{ left: `${8 + index * 24}%`, top: `${32 + (index % 2 === 0 ? 0 : 17)}%` }} key={node.id} onClick={() => setSelected(node.id)}><div className={`${styles.workflowNodeIcon} ${styles[`nodeTone${node.tone}`]}`}><node.icon size={17} /></div><div><strong>{node.title}</strong><small>{node.detail}</small></div><span className={styles.nodeState}>{running ? "运行中" : index < 2 ? "已配置" : "待运行"}</span></div>)}<div className={`${styles.connector} ${styles.connectorOne}`} /><div className={`${styles.connector} ${styles.connectorTwo}`} /><div className={`${styles.connector} ${styles.connectorThree}`} /><div className={styles.canvasHint}><GitBranch size={15} />可视化编排预览</div></div><aside className={styles.nodeInspector}><div className={styles.inspectorTitle}><span className={styles.sectionEyebrow}>NODE CONFIGURATION</span><h2>节点配置</h2></div><div className={styles.selectedNode}><div className={styles.selectedNodeIcon}><Search size={18} /></div><div><strong>{nodes.find((node) => node.id === selected)?.title}</strong><small>{nodes.find((node) => node.id === selected)?.detail}</small></div></div><label>节点说明<textarea value={`负责将输入文件中的关键要求与制度知识库进行关联检索，输出可追溯的引用片段。`} readOnly rows={5} /></label><div className={styles.parameterRow}><span>执行顺序</span><strong>步骤 03 / 04</strong></div><div className={styles.parameterRow}><span>失败策略</span><strong>重试 2 次</strong></div><button className={styles.buttonSecondaryWide} type="button" onClick={() => setNotice({ tone: "info", text: "节点编辑面板将在后续版本开放。" })}><Settings2 size={14} />编辑节点参数</button></aside></div>
  </PageShell>;
}

function DocsMockPage() {
  return <PageShell eyebrow="PLATFORM" title="文档中心" description="查看工作台的使用说明、接口约定和版本记录。"><div className={styles.resourceGrid}><ResourceCard icon={FileText} title="产品使用说明" description="了解知识库、智能体和任务的基本工作流。" /><ResourceCard icon={Code2} title="API 接入约定" description="统一 Axios、React Query 和后端接口边界。" /><ResourceCard icon={GitBranch} title="LangChain 接入说明" description="查看前端与后端 Agent 编排的职责边界。" /><ResourceCard icon={FileClock} title="版本更新记录" description="记录当前 mock 设计和后续接入计划。" /></div><Panel title="当前设计基线"><div className={styles.baselineList}><div><CheckCircle2 size={16} /><span>工作台导航和页面路由已固定</span><Tag label="已完成" tone="green" /></div><div><CheckCircle2 size={16} /><span>知识库、对话、Tender Agent UI 已具备 mock 入口</span><Tag label="已完成" tone="green" /></div><div><Clock3 size={16} /><span>后端 API 契约接入与真实状态恢复</span><Tag label="待接入" tone="amber" /></div></div></Panel></PageShell>;
}

function SettingsMockPage() {
  const [enabled, setEnabled] = useState(true);
  return <PageShell eyebrow="PLATFORM" title="系统设置" description="管理工作区默认偏好和服务显示选项。当前设置仅保存在页面状态中。"><div className={styles.settingsGrid}><Panel title="工作区偏好" icon={<Settings2 size={16} />}><div className={styles.settingsList}><SettingToggle label="显示任务运行状态" description="在顶部导航和任务列表显示实时状态。" enabled={enabled} onChange={() => setEnabled((value) => !value)} /><SettingToggle label="自动展开最近任务" description="进入控制台时优先展示最近处理记录。" enabled /><SettingToggle label="启用知识库引用提示" description="在对话和检索结果中显示引用来源。" enabled /></div></Panel><Panel title="服务状态" icon={<Activity size={16} />}><div className={styles.serviceList}><ServiceStatus label="知识库服务" detail="API / Retrieval" /><ServiceStatus label="Agent Runtime" detail="Mock Adapter" /><ServiceStatus label="文件存储" detail="Local Workspace" /></div></Panel></div><div className={styles.settingsFooter}><span>配置版本 v0.1 · UI mock</span><button className={styles.buttonPrimary} type="button">保存设置</button></div></PageShell>;
}

function PageShell({ eyebrow, title, description, actions, notice, children }: { eyebrow: string; title: string; description: string; actions?: React.ReactNode; notice?: Notice; children: React.ReactNode }) {
  return <div className={styles.page}><div className={styles.heading}><div><div className={styles.eyebrow}>{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{actions && <div className={styles.headingActions}>{actions}</div>}</div>{notice && <div className={`${styles.notice} ${notice.tone === "success" ? styles.noticeSuccess : styles.noticeInfo}`}><CheckCircle2 size={15} />{notice.text}</div>}{children}</div>;
}

function Panel({ title, icon, action, className, children }: { title: string; icon?: React.ReactNode; action?: React.ReactNode; className?: string; children: React.ReactNode }) {
  return <section className={`${styles.panel} ${className ?? ""}`}><div className={styles.panelHeading}><div className={styles.panelTitle}>{icon}<h2>{title}</h2></div>{action}</div>{children}</section>;
}

function StatCard({ icon: Icon, tone, label, value, note }: { icon: typeof Activity; tone: "blue" | "green" | "purple" | "amber"; label: string; value: string; note: string }) {
  return <div className={styles.statCard}><div className={`${styles.statIcon} ${styles[`tone${tone}`]}`}><Icon size={18} /></div><div className={styles.statCopy}><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>;
}

function QuickStartCard({ icon: Icon, title, description, onClick }: { icon: typeof Activity; title: string; description: string; onClick: () => void }) {
  return <button className={styles.quickStartCard} type="button" onClick={onClick}><div className={styles.quickStartIcon}><Icon size={17} /></div><div><strong>{title}</strong><span>{description}</span></div><ArrowRight size={15} /></button>;
}

function AgentCard({ agent, onOpen }: { agent: typeof agentCards[number]; onOpen: () => void }) {
  const Icon = agent.icon;
  return <article className={styles.agentCard}><div className={styles.agentCardTop}><div className={`${styles.agentCardIcon} ${styles[`tone${agent.tone}`]}`}><Icon size={19} /></div><StatusPill label={agent.status} tone={agent.tone === "green" ? "green" : "amber"} /></div><h3>{agent.name}</h3><p>{agent.description}</p><div className={styles.agentCardFooter}><span>最近运行 · 12 分钟前</span><button className={styles.textAction} type="button" onClick={onOpen}>打开 <ChevronRight size={13} /></button></div></article>;
}

function TaskTable({ onOpen, tenderOnly = false }: { onOpen: (task: typeof recentTasks[number]) => void; tenderOnly?: boolean }) {
  const tasks = tenderOnly ? recentTasks.filter((task) => task.agent === "Tender Agent") : recentTasks;
  return <div className={styles.taskTable}><div className={styles.taskTableHeader}><span>任务</span><span>智能体</span><span>状态</span><span>时间</span><span>耗时</span><span /></div>{tasks.map((task) => <button className={styles.taskRow} type="button" key={task.id} onClick={() => onOpen(task)}><div><strong>{task.title}</strong><small>{task.id}</small></div><span>{task.agent}</span><StatusPill label={task.status} tone={task.tone === "blue" ? "blue" : task.tone === "green" ? "green" : "amber"} /><span>{task.time}</span><span>{task.duration}</span><ChevronRight size={14} /></button>)}</div>;
}

function StatusPill({ label, tone }: { label: string; tone: "green" | "blue" | "amber" | "gray" }) { return <span className={`${styles.statusPill} ${styles[`status${tone}`]}`}><i />{label}</span>; }

function Checklist({ items }: { items: string[] }) { return <div className={styles.checklist}>{items.map((item, index) => <div key={item}><span className={index === 0 ? styles.checkPending : styles.checkDone}>{index === 0 ? <Clock3 size={13} /> : <Check size={13} />}</span><span>{item}</span><small>{index === 0 ? "待确认" : "已准备"}</small></div>)}</div>; }

function DetailRow({ label, value }: { label: string; value: string }) { return <div className={styles.detailRow}><span>{label}</span><strong>{value}</strong></div>; }

function TimelineItem({ time, title, detail, done }: { time: string; title: string; detail: string; done?: boolean }) { return <div className={styles.timelineItem}><div className={styles.timelineMarker}>{done ? <Check size={12} /> : <Clock3 size={12} />}</div><div><strong>{title}</strong><p>{detail}</p></div><time>{time}</time></div>; }

function Tag({ label, tone }: { label: string; tone: "green" | "blue" | "amber" | "gray" }) { return <span className={`${styles.tag} ${styles[`tag${tone}`]}`}>{label}</span>; }

function Placeholder({ label, type }: { label: string; type: string }) { return <div className={styles.placeholder}><div><strong>{label}</strong><small>{type}</small></div><span>待补充</span></div>; }

function ResourceCard({ icon: Icon, title, description }: { icon: typeof Activity; title: string; description: string }) { return <button className={styles.resourceCard} type="button"><div className={styles.resourceIcon}><Icon size={18} /></div><div><strong>{title}</strong><p>{description}</p></div><ArrowRight size={15} /></button>; }

function SettingToggle({ label, description, enabled: initialEnabled, onChange }: { label: string; description: string; enabled?: boolean; onChange?: () => void }) { const [enabled, setEnabled] = useState(initialEnabled ?? false); const checked = onChange ? initialEnabled : enabled; return <div className={styles.settingRow}><div><strong>{label}</strong><p>{description}</p></div><button className={`${styles.toggle} ${checked ? styles.toggleOn : ""}`} type="button" onClick={onChange ?? (() => setEnabled((value) => !value))} aria-label={label}><span /></button></div>; }

function ServiceStatus({ label, detail }: { label: string; detail: string }) { return <div className={styles.serviceRow}><div><strong>{label}</strong><small>{detail}</small></div><StatusPill label="正常" tone="green" /></div>; }
