import React, { useEffect, useState } from "react";
import { checkHealth, getSlots, getThread, sendMessage } from "./api";

function NodeBadge({ node, status }) { return <div className="status-row"><div className="badge"><span className="pulse" /> {node}</div><span className={`status status-${status}`}>{status === "idle" ? "Ready" : status.replace("_", " ")}</span></div>; }
function MessageBubble({ message }) {
  return <div className={`message ${message.role}`}><div className="message-label">{message.role === "user" ? "You" : "HR Assistant"}</div><div>{message.content}</div>{message.citations?.map((c) => <span className="citation" key={c.page}>📄 Page {c.page}</span>)}</div>;
}

export default function App() {
  const [threadId, setThreadId] = useState(() => localStorage.getItem("thread_id") || crypto.randomUUID());
  const [messages, setMessages] = useState([]);
  const [slots, setSlots] = useState([]);
  const [input, setInput] = useState("");
  const [node, setNode] = useState("Router");
  const [status, setStatus] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [online, setOnline] = useState(false);
  useEffect(() => {
    localStorage.setItem("thread_id", threadId);
    getThread(threadId).then((data) => { if (data) { setMessages(data.messages); setStatus(data.booking?.status || "idle"); } });
    getSlots().then(setSlots).catch(() => setError("Backend is offline. Start the FastAPI server, then retry."));
    checkHealth().then(() => setOnline(true)).catch(() => setOnline(false));
  }, [threadId]);
  async function submit(text = input) {
    if (!text.trim() || loading) return;
    setError(""); setLoading(true); setMessages((old) => [...old, {role: "user", content: text}]); setInput("");
    try { const result = await sendMessage({thread_id: threadId, message: text}); setMessages((old) => [...old, {role: "assistant", content: result.reply, citations: result.citations}]); setNode(result.active_node); setStatus(result.booking_status); setSlots(await getSlots()); }
    catch (e) { setError(e.message); setOnline(false); } finally { setLoading(false); }
  }
  function newChat() { setThreadId(crypto.randomUUID()); setMessages([]); setStatus("idle"); setNode("Router"); setError(""); }
  async function copyThread() { await navigator.clipboard?.writeText(threadId); }
  return <main><header><div className="brand"><div className="logo">N</div><div><h1>Northwind HR Assistant</h1><small>Policy answers and 1-on-1 scheduling</small></div></div><div className="header-actions"><span className={`connection ${online ? "online" : ""}`}><span /> {online ? "API online" : "API offline"}</span><button className="ghost" onClick={copyThread}>Copy thread</button><button onClick={newChat}>＋ New chat</button></div></header>
    <section className="layout"><div className="chat"><NodeBadge node={node} status={status}/><div className="thread-line">Thread <code>{threadId}</code></div><div className="messages">{messages.length === 0 && <div className="welcome"><div className="welcome-icon">✦</div><h2>How can I help today?</h2><p>Ask about Northwind policies or start a booking. I’ll remember your details if you switch topics.</p></div>}{messages.map((m, i) => <MessageBubble message={m} key={i}/>)}{loading && <div className="message assistant typing"><div className="message-label">HR Assistant</div><span className="dots"><i /><i /><i /></span></div>}</div>
      {error && <div className="error"><span>⚠</span><div><strong>Couldn’t connect</strong><br />{error}</div><button className="retry" onClick={() => submit(input)}>Retry</button></div>}
      <div className="suggestions"><button onClick={() => submit("Book a Performance Review")}>📅 Book a review</button><button onClick={() => submit("How many PTO days do I get?")}>📘 Ask about PTO</button><button onClick={() => submit("How often are performance reviews conducted?")}>❔ Review policy</button></div>
      <form onSubmit={(e) => {e.preventDefault(); submit();}}><input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question or type a message…" maxLength={2000} disabled={loading}/><span className="char-count">{input.length}/2000</span><button disabled={loading || !input.trim()}>{loading ? "…" : "Send  ➤"}</button></form>
    </div><aside><div className="aside-title"><div><h2>Available slots</h2><p>Times are shown in IST</p></div><span className="calendar">▦</span></div>{slots.length === 0 ? <div className="empty-slots">No slots available right now.</div> : slots.map((slot, index) => <button className="slot" key={slot.slot_id} onClick={() => setInput(`I'd like slot ${index + 1}`)}><span className="slot-number">{index + 1}</span><span>{slot.label}</span><span className="arrow">→</span></button>)}<div className="privacy">🔒 Your conversation is saved to this thread only.</div></aside></section></main>;
}
