const cards = [
  {
    title: "知识库维护",
    description: "后续用于管理制度样板、收费标准、版本和入库状态。"
  },
  {
    title: "RAG 检索调试",
    description: "后续用于展示 chunk 召回结果、引用来源和命中片段。"
  },
  {
    title: "LLM 问答验证",
    description: "后续用于验证基于知识库的问答效果和答案回溯。"
  }
];

export default function App() {
  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">Bid Document Agent</p>
        <h1>RAG MVP Workspace</h1>
        <p className="lede">
          这里是前端 React 工程入口。当前阶段将围绕公司制度和收费标准样板，
          逐步补齐知识库维护、RAG 检索展示和 LLM 问答验证界面。
        </p>
      </section>

      <section className="grid">
        {cards.map((card) => (
          <article key={card.title} className="card">
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}
