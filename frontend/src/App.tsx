import { useState, type FormEvent } from "react";

type Stage = { label: string; detail: string; status: "completed" | "pending" };
type TaskResult = { product_summary: { name: string; category: string }; rewritten: { title: string; body: string } };

const stages: Stage[] = [
  { label: "素材分析", detail: "提取商品属性与场景", status: "completed" },
  { label: "文案生成", detail: "生成 3 版小红书草案", status: "completed" },
  { label: "内容审核", detail: "识别平台表达风险", status: "completed" },
  { label: "自动改写", detail: "输出可编辑合规版本", status: "completed" },
];

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [brief, setBrief] = useState("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<TaskResult | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) return setError("请先选择商品图片。");
    if (!brief.trim()) return setError("请填写本次内容目标，例如“突出下午茶和便携”。");
    setError("");
    setSubmitting(true);
    try {
      const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const formData = new FormData();
      formData.append("file", file);
      const uploadResponse = await fetch(`${base}/api/uploads`, { method: "POST", body: formData });
      if (!uploadResponse.ok) throw new Error("图片上传失败，请检查文件格式和大小。");
      const upload = await uploadResponse.json();
      const taskResponse = await fetch(`${base}/api/tasks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ asset_id: upload.asset_id, platform: "xiaohongshu", category: "snack", brief }) });
      if (!taskResponse.ok) throw new Error("任务创建失败，请稍后重试。");
      const task = await taskResponse.json();
      setResult(task.result);
      setSubmitted(true);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "任务提交失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand-mark">OC</div>
        <div><p className="eyebrow">OPERATIONCOPILOT / MILESTONE 1</p><h1>内容运营工作台</h1></div>
        <span className="scope-badge">小红书 · 零食</span>
      </header>

      <section className="hero">
        <div><p className="eyebrow accent">CONTENT OPS, WITHOUT THE BLANK PAGE</p><h2>把一张商品图，<br /><em>变成可发布的内容方向。</em></h2><p className="hero-copy">上传素材，告诉我这次想强调什么。OperationCopilot 会沿着分析、生成、审核和改写的路径，整理出一组可继续编辑的内容草案。</p></div>
        <div className="hero-note"><span>01</span><p>先跑通一条真实业务闭环<br /><strong>图片 → 文案 → 审核 → 改写</strong></p></div>
      </section>

      <section className="workspace-grid">
        <form className="panel form-panel" onSubmit={submit} noValidate>
          <div className="panel-heading"><div><p className="eyebrow">START HERE</p><h3>创建分析任务</h3></div><span className="required-note">* 必填</span></div>
          <label htmlFor="asset">商品图片 <span>*</span></label>
          <label className="dropzone" htmlFor="asset"><input id="asset" type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => { setFile(event.target.files?.[0] ?? null); setError(""); }} /> <strong>{file ? file.name : "点击选择或拖入商品图片"}</strong><small>PNG / JPEG / WebP · 最大 10 MB</small></label>
          <label htmlFor="brief">内容目标 <span>*</span></label>
          <textarea id="brief" value={brief} onChange={(event) => setBrief(event.target.value)} placeholder="例如：突出下午茶场景、便携包装和轻松分享感" rows={4} />
          {error && <p className="error" role="alert">{error}</p>}
          <button className="primary-button" type="submit" disabled={submitting}>{submitting ? "正在分析…" : submitted ? "任务已提交 · 查看结果" : "开始分析任务"}<span>↗</span></button>
          <p className="privacy-note">本阶段为本地演示，素材不会发布到任何平台。</p>
        </form>

        <section className="panel flow-panel" aria-labelledby="flow-title"><div className="panel-heading"><div><p className="eyebrow">WORKFLOW</p><h3 id="flow-title">处理路径</h3></div><span className="status-chip">{submitted ? "任务完成" : "待提交"}</span></div><div className="stage-list">{stages.map((stage, index) => <div className={`stage ${submitted ? "done" : ""}`} key={stage.label}><div className="stage-line"><span className="stage-number">0{index + 1}</span><span className="stage-dot">{submitted ? "✓" : "·"}</span></div><div><strong>{stage.label}</strong><p>{stage.detail}</p></div></div>)}</div><div className="flow-footer"><span className="pulse" />{submitted ? "模拟工作流已完成" : "提交后将按顺序执行"}</div></section>
      </section>

      <section className={`panel result-panel ${submitted ? "visible" : ""}`} aria-live="polite"><div className="result-heading"><div><p className="eyebrow accent">RESULT PREVIEW</p><h3>{submitted ? "一份可继续编辑的内容草案" : "结果将在这里出现"}</h3></div>{submitted && <span className="success-label">✓ 已完成</span>}</div>{submitted && result ? <div className="result-grid"><div><p className="result-label">商品摘要</p><h4>{result.product_summary.name}</h4><p className="muted">{result.product_summary.category} · 酥脆口感 · 便携包装 · 办公 / 下午茶</p><div className="quote">“把下午茶的期待，交给这一口轻松的酥脆。”</div></div><div><p className="result-label">审核提醒</p><div className="risk-card"><span>中风险</span><p><strong>“0添加”</strong> 当前缺少资料支撑，建议改为配料表可核验的具体表述。</p></div><p className="result-label rewrite-label">自动改写</p><p><strong>{result.rewritten.title}</strong><br />{result.rewritten.body}</p></div></div> : <p className="empty-copy">完成左侧任务后，这里会展示商品属性、三版候选文案、审核风险和自动改写结果。</p>}</section>
      <footer><span>OperationCopilot</span><span>Milestone 1 · Foundation</span></footer>
    </main>
  );
}
