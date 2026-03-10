import { useState, useRef, useEffect, useCallback } from 'react'
import './index.css'

// ── Config ─────────────────────────────────────────────────
// In production, set VITE_API_URL to your deployed backend URL.
// In development (npm run dev), Vite proxy forwards /api/* to the FastAPI server.
const API_BASE = import.meta.env.VITE_API_URL || ''

const api = {
  chat: (body) =>
    fetch(`${API_BASE}/qa/conversation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  uploadPdf: (formData) =>
    fetch(`${API_BASE}/index-pdf`, { method: 'POST', body: formData }),
}

// ── Helpers ─────────────────────────────────────────────────
function genSessionId() {
  return 'sess_' + Math.random().toString(36).slice(2, 10)
}

function loadSession() {
  try {
    return JSON.parse(localStorage.getItem('ikms_session') || 'null')
  } catch {
    return null
  }
}

function saveSession(session) {
  localStorage.setItem('ikms_session', JSON.stringify(session))
}

function clearSession() {
  localStorage.removeItem('ikms_session')
}

// ── Sub-components ──────────────────────────────────────────

function ThinkingIndicator() {
  return (
    <div className="thinking-indicator">
      <div className="ai-avatar">🤖</div>
      <div className="thinking-dots">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Thinking…</span>
    </div>
  )
}

function MessageBubble({ msg }) {
  return (
    <div className="message-row">
      {/* User bubble */}
      <div className="user-message">{msg.question}</div>

      {/* AI bubble */}
      <div className="ai-message">
        <div className="ai-bubble">
          <div className="ai-header">
            <div className="ai-avatar">🤖</div>
            <span className="ai-label">IKMS Assistant</span>
            <span className="turn-badge">Turn {msg.turn}</span>
            {msg.usedHistory && (
              <span className="history-used-badge">
                ℹ️ Using conversation context
              </span>
            )}
          </div>

          <div className="answer-text">{msg.answer}</div>
        </div>

        {/* Expandable context */}
        {msg.context && (
          <div className="context-accordion">
            <details>
              <summary>📄 View Retrieved Context</summary>
              <pre className="context-content">{msg.context}</pre>
            </details>
          </div>
        )}
      </div>
    </div>
  )
}

function PdfUpload({ apiBase }) {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState(null) // {type:'success'|'error', msg}
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) return
    setLoading(true)
    setStatus(null)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await api.uploadPdf(fd)
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')
      setStatus({ type: 'success', msg: `✅ Indexed ${data.chunks_indexed} chunks from "${data.filename}"` })
      setFile(null)
    } catch (err) {
      setStatus({ type: 'error', msg: `❌ ${err.message}` })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="upload-section">
      <button className="upload-toggle" onClick={() => setOpen(o => !o)}>
        {open ? '▲ Hide PDF Upload' : '📎 Upload PDF to Knowledge Base'}
      </button>
      {open && (
        <div className="upload-panel">
          <input
            type="file"
            accept=".pdf"
            onChange={e => setFile(e.target.files[0])}
          />
          <button
            className="upload-btn"
            onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? 'Uploading…' : 'Index PDF'}
          </button>
          {status && (
            <div className={`upload-status ${status.type}`}>{status.msg}</div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Main App ────────────────────────────────────────────────
export default function App() {
  // Session state (persisted to localStorage)
  const [sessionId, setSessionId] = useState(() => {
    const saved = loadSession()
    return saved?.sessionId || genSessionId()
  })
  const [history, setHistory] = useState(() => {
    const saved = loadSession()
    return saved?.history || []
  })
  const [conversationSummary, setConversationSummary] = useState(() => {
    const saved = loadSession()
    return saved?.conversationSummary || null
  })

  // UI state
  const [messages, setMessages] = useState(() => {
    const saved = loadSession()
    return saved?.messages || []
  })
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const messagesEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Persist session to localStorage whenever it changes
  useEffect(() => {
    saveSession({ sessionId, history, conversationSummary, messages })
  }, [sessionId, history, conversationSummary, messages])

  const startNewSession = useCallback(() => {
    const newId = genSessionId()
    setSessionId(newId)
    setHistory([])
    setConversationSummary(null)
    setMessages([])
    setError(null)
    clearSession()
  }, [])

  const handleSend = useCallback(async () => {
    const q = question.trim()
    if (!q || loading) return

    setQuestion('')
    setError(null)
    setLoading(true)

    // Optimistic UI — add thinking placeholder
    const optimisticId = Date.now()

    try {
      const res = await api.chat({
        question: q,
        session_id: sessionId,
        history: history,
        conversation_summary: conversationSummary,
      })

      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || `API error ${res.status}`)
      }

      // Update history state with what the server returned
      setHistory(data.updated_history || [...history])
      if (data.conversation_summary) {
        setConversationSummary(data.conversation_summary)
      }

      // Add message to chat UI
      setMessages(prev => [
        ...prev,
        {
          id: optimisticId,
          turn: data.turn_number,
          question: q,
          answer: data.answer,
          context: data.context,
          usedHistory: data.used_history,
        },
      ])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [question, loading, sessionId, history, conversationSummary])

  // Auto-resize textarea
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = (e) => {
    const ta = textareaRef.current
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
    setQuestion(e.target.value)
  }

  const hasConversation = messages.length > 0

  return (
    <div className="app-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">🧠</div>
          <div>
            <h2>IKMS</h2>
            <span>Multi-Agent RAG</span>
          </div>
        </div>

        <button className="new-chat-btn" onClick={startNewSession}>
          ✏️ New Conversation
        </button>

        {/* Session Info */}
        <div className="sidebar-section-label">Current Session</div>
        <div className="session-info">
          <div className="label">Session ID</div>
          <div className="session-id-text">{sessionId}</div>
          <div className="label" style={{ marginTop: '0.5rem' }}>
            Turns: {history.length}
          </div>
        </div>

        {/* Memory status */}
        {conversationSummary && (
          <>
            <div className="sidebar-section-label">Memory</div>
            <div className="memory-badge">
              📝 Conversation summarized
            </div>
            <div className="memory-accordion">
              <details>
                <summary style={{ padding: '0.5rem 0.75rem', cursor: 'pointer', fontSize: '0.75rem', color: 'var(--accent)', display: 'flex', gap: '0.4rem', alignItems: 'center', listStyle: 'none' }}>
                  View Summary
                </summary>
                <div style={{ padding: '0.5rem 0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)', borderTop: '1px solid var(--border)', whiteSpace: 'pre-wrap', maxHeight: '180px', overflowY: 'auto' }}>
                  {conversationSummary}
                </div>
              </details>
            </div>
          </>
        )}

        {/* History list */}
        {hasConversation && (
          <>
            <div className="sidebar-section-label">This Session</div>
            <div className="history-list">
              {messages.map((msg) => (
                <div key={msg.id} className="history-item">
                  <div className="history-item-turn">Turn {msg.turn}</div>
                  <div className="history-item-question">{msg.question}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </aside>

      {/* ── Chat Area ── */}
      <main className="chat-area">
        <header className="chat-header">
          <h1>Conversational AI Assistant <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 400 }}>Feature 5</span></h1>
          <div className="chat-header-meta">
            <div className="status-dot" />
            <span>Multi-agent RAG • LangGraph</span>
          </div>
        </header>

        {/* Messages */}
        <div className="messages-container">
          {!hasConversation && !loading ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🧠</div>
              <h2>Ask me anything</h2>
              <p>
                I remember our conversation across multiple turns. Ask follow-up
                questions using pronouns like "it" or "that" — I'll always know
                what you're referring to.
              </p>
              <div className="welcome-features">
                <span className="feature-chip">💬 Multi-turn memory</span>
                <span className="feature-chip">🔍 Vector search</span>
                <span className="feature-chip">🧩 LangGraph RAG</span>
                <span className="feature-chip">📝 Auto-summarization</span>
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}

              {loading && <ThinkingIndicator />}

              {error && (
                <div className="error-toast">
                  ⚠️ {error}
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="input-area">
          <div className="input-row">
            <textarea
              ref={textareaRef}
              className="question-input"
              placeholder="Ask a question about your documents… (Shift+Enter for new line)"
              value={question}
              onInput={handleInput}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              className="send-btn"
              onClick={handleSend}
              disabled={!question.trim() || loading}
            >
              {loading ? '⏳' : 'Send →'}
            </button>
          </div>
          <div className="input-hint">
            {hasConversation
              ? `Turn ${messages.length + 1} • History-aware retrieval active`
              : 'Start by asking a question about your indexed documents'}
          </div>

          <PdfUpload />
        </div>
      </main>
    </div>
  )
}
