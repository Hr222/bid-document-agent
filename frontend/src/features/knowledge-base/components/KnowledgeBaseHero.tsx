import { ArrowRight, Search, Upload, Workflow } from "lucide-react";
import { Button } from "antd";

import styles from "../pages/KnowledgeBasePage.module.css";

export function KnowledgeBaseHero({ onUpload, onSearch }: { onUpload: () => void; onSearch: () => void }) {
  return <section className={styles.hero}><div className={styles.heroGlow} /><div className={styles.heroContent}><div className={styles.heroKicker}>KNOWLEDGE FOUNDATION <span>·</span> 制度知识库</div><h2>让每一份制度，都能被准确找到。</h2><p>文档经过解析、清洗、切块和向量化后，成为 Agent 可以引用的企业事实。</p><SpaceActions onUpload={onUpload} onSearch={onSearch} /></div><div className={styles.heroVisual}><div className={styles.orbitOne} /><div className={styles.orbitTwo} /><div className={styles.visualCore}><Workflow size={29} /></div><span className={`${styles.visualPill} ${styles.pillOne}`}>解析</span><span className={`${styles.visualPill} ${styles.pillTwo}`}>检索</span><span className={`${styles.visualPill} ${styles.pillThree}`}>引用</span></div></section>;
}

function SpaceActions({ onUpload, onSearch }: { onUpload: () => void; onSearch: () => void }) {
  return <div className={styles.heroActions}><Button type="primary" icon={<Upload size={14} />} onClick={onUpload}>导入第一份文档</Button><Button type="text" icon={<Search size={14} />} onClick={onSearch}>试试知识检索 <ArrowRight size={13} /></Button></div>;
}
