import { Activity, Clock3, Database, Layers3 } from "lucide-react";
import { Card, Col, Row, Statistic, Tag } from "antd";

import type { KnowledgeBaseOverview } from "../types";
import styles from "../pages/KnowledgeBasePage.module.css";

const iconMap = {
  blue: <Database size={18} />,
  purple: <Layers3 size={18} />,
  green: <Activity size={18} />,
  amber: <Clock3 size={18} />,
} as const;

export function KnowledgeBaseStats({ overview, loading }: { overview?: KnowledgeBaseOverview; loading: boolean }) {
  const cards = [
    { label: "知识库文档", value: overview?.documentCount ?? 0, suffix: "个文件", tone: "blue" as const, note: "较上月 +12%" },
    { label: "向量切片", value: overview?.chunkCount ?? 0, suffix: "Chunks", tone: "purple" as const, note: "索引已同步" },
    { label: "检索可用率", value: overview?.retrievalAvailability ?? 0, suffix: "%", tone: "green" as const, note: "过去 30 天" },
    { label: "待处理任务", value: overview?.pendingCount ?? 0, suffix: "个", tone: "amber" as const, note: overview?.failedCount ? `${overview.failedCount} 个需要关注` : "暂无异常" },
  ];

  return <Row gutter={[16, 16]} className={styles.statsGrid}>{cards.map((card) => <Col xs={24} sm={12} xl={6} key={card.label}><Card loading={loading} className={styles.statCard}><div className={`${styles.statIcon} ${styles[card.tone]}`}>{iconMap[card.tone]}</div><div className={styles.statCopy}><Statistic title={card.label} value={card.value} suffix={card.suffix} /><Tag className={styles.statNote} color={card.tone === "amber" ? "warning" : card.tone === "green" ? "success" : "processing"}>{card.note}</Tag></div></Card></Col>)}</Row>;
}
