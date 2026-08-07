import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ThumbsUp, ThumbsDown, Zap, Cpu, DollarSign, Sparkles, AlertCircle } from 'lucide-react';
import { ChatMessage, ChatResponse } from '../types';

interface PlaygroundProps {
  onMessageSent: (response: ChatResponse) => void;
}

const PRESETS = [
  { label: "⚡ Simple QA", prompt: "What is the capital of France?" },
  { label: "📊 SQL Query", prompt: "Write a PostgreSQL query to find the top 5 customers with the highest total order values in 2024." },
  { label: "🧠 System Architecture", prompt: "Design a high-throughput microservice architecture using Redis, Kafka, PostgreSQL, and FastAPI. Explain trade-offs." }
];

export const Playground: React.FC<PlaygroundProps> = ({ onMessageSent }) => {
  const [input, setInput] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'bot',
      text: 'Hello! I am your LLM Cost Autopilot Gateway. Send me any prompt and watch how I dynamically route your request to the most cost-effective LLM based on ML complexity scoring!',
      timestamp: new Date()
    }
  ]);
  const [selectedMeta, setSelectedMeta] = useState<ChatResponse | null>(null);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<number, 'up' | 'down'>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (overridePrompt?: string) => {
    const promptToSend = overridePrompt || input;
    if (!promptToSend.trim() || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: promptToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    if (!overridePrompt) setInput('');
    setLoading(true);

    try {
      const res = await fetch('/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: promptToSend,
          system_prompt: systemPrompt.trim() || undefined
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }

      const data: ChatResponse = await res.json();

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: data.response,
        timestamp: new Date(),
        metadata: data
      };

      setMessages(prev => [...prev, botMsg]);
      setSelectedMeta(data);
      onMessageSent(data);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'bot',
        text: `⚠️ Gateway Error: ${err.message || 'Failed to connect to router API.'}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const submitFeedback = async (logId: number, type: 'up' | 'down') => {
    try {
      await fetch('/v1/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          log_id: logId,
          feedback: type === 'up' ? 'positive' : 'negative'
        })
      });
      setFeedbackGiven(prev => ({ ...prev, [logId]: type }));
    } catch (e) {
      console.error("Feedback error", e);
    }
  };

  const getBadgeClass = (label: string) => {
    switch (label) {
      case 'LOW': return 'badge-low';
      case 'MEDIUM': return 'badge-medium';
      case 'HIGH': return 'badge-high';
      case 'CACHED': return 'badge-cached';
      default: return 'badge-low';
    }
  };

  return (
    <div className="chat-container">
      {/* Main Chat Panel */}
      <div className="chat-box glass">
        {/* Preset Header */}
        <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid var(--bg-card-border)', display: 'flex', gap: '0.5rem', alignItems: 'center', background: 'rgba(17, 24, 39, 0.4)' }}>
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 500 }}>Presets:</span>
          {PRESETS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p.prompt)}
              disabled={loading}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--bg-card-border)',
                borderRadius: 'var(--radius-sm)',
                padding: '0.25rem 0.6rem',
                color: 'var(--text-main)',
                fontSize: '0.75rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Message Stream */}
        <div className="messages-list">
          {messages.map(msg => (
            <div key={msg.id} className={`message-bubble ${msg.sender === 'user' ? 'message-user' : 'message-bot'}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                {msg.sender === 'user' ? (
                  <><span>You</span><User className="w-3.5 h-3.5" /></>
                ) : (
                  <><Bot className="w-3.5 h-3.5 text-indigo-400" /><span>Autopilot Gateway</span></>
                )}
                {msg.metadata && (
                  <span className={`badge ${getBadgeClass(msg.metadata.complexity_label)}`}>
                    {msg.metadata.complexity_label}
                  </span>
                )}
              </div>

              <div
                className="bubble-content"
                onClick={() => msg.metadata && setSelectedMeta(msg.metadata)}
                style={{ cursor: msg.metadata ? 'pointer' : 'default' }}
              >
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
              </div>

              {/* Bot Meta Quick Bar */}
              {msg.metadata && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                    <span>Model: <strong style={{ color: 'var(--accent-secondary)' }}>{msg.metadata.model_used}</strong></span>
                    <span>Cost: <strong style={{ color: 'var(--success)' }}>${msg.metadata.cost.toFixed(5)}</strong></span>
                  </div>

                  {msg.metadata.log_id && (
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button
                        onClick={() => submitFeedback(msg.metadata!.log_id!, 'up')}
                        style={{ background: 'none', border: 'none', color: feedbackGiven[msg.metadata.log_id!] === 'up' ? 'var(--success)' : 'var(--text-dim)', cursor: 'pointer' }}
                      >
                        <ThumbsUp className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => submitFeedback(msg.metadata!.log_id!, 'down')}
                        style={{ background: 'none', border: 'none', color: feedbackGiven[msg.metadata.log_id!] === 'down' ? 'var(--danger)' : 'var(--text-dim)', cursor: 'pointer' }}
                      >
                        <ThumbsDown className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message-bubble message-bot">
              <div className="bubble-content" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                <Zap className="w-4 h-4 animate-spin text-indigo-400" />
                <span>Evaluating prompt features & selecting optimal model...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="chat-input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="Type your prompt here..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            disabled={loading}
          />
          <button className="btn-send" onClick={() => handleSend()} disabled={loading || !input.trim()}>
            <span>Route Prompt</span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Sidebar - Route Analytics Inspector */}
      <div className="sidebar-panel glass">
        <h3 className="panel-title">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <span>Routing Inspector</span>
        </h3>

        {selectedMeta ? (
          <>
            <div className="glass-card" style={{ padding: '1rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Complexity Decision</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.5rem' }}>
                <span className={`badge ${getBadgeClass(selectedMeta.complexity_label)}`}>
                  {selectedMeta.complexity_label}
                </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '1.1rem', fontWeight: 700 }}>
                  Score: {selectedMeta.complexity_score.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="glass-card" style={{ padding: '1rem' }}>
              <div className="metric-row">
                <span className="label">Selected Model</span>
                <span className="value" style={{ color: 'var(--accent-secondary)' }}>{selectedMeta.model_used}</span>
              </div>
              <div className="metric-row">
                <span className="label">Provider</span>
                <span className="value">{selectedMeta.provider}</span>
              </div>
              <div className="metric-row">
                <span className="label">Prompt Tokens</span>
                <span className="value">{selectedMeta.prompt_tokens}</span>
              </div>
              <div className="metric-row">
                <span className="label">Completion Tokens</span>
                <span className="value">{selectedMeta.completion_tokens}</span>
              </div>
              <div className="metric-row">
                <span className="label">Actual Cost</span>
                <span className="value" style={{ color: 'var(--text-main)' }}>${selectedMeta.cost.toFixed(6)}</span>
              </div>
              <div className="metric-row">
                <span className="label">Estimated Savings</span>
                <span className="value" style={{ color: 'var(--success)' }}>+${selectedMeta.savings.toFixed(6)}</span>
              </div>
            </div>

            {selectedMeta.explanation && (
              <div className="glass-card" style={{ padding: '1rem' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: '0.75rem', color: 'var(--text-main)' }}>
                  Extracted Features Breakdown
                </div>
                {Object.entries(selectedMeta.explanation).map(([feat, score]) => (
                  <div key={feat} style={{ marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>{feat.replace('_', ' ')}</span>
                      <span>{score.toFixed(2)}</span>
                    </div>
                    <div style={{ height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden', marginTop: '3px' }}>
                      <div style={{ height: '100%', width: `${Math.min(100, score * 10)}%`, background: 'var(--accent-gradient)' }} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)', textAlign: 'center', gap: '0.75rem' }}>
            <AlertCircle className="w-8 h-8 text-indigo-400 opacity-50" />
            <p style={{ fontSize: '0.875rem' }}>Select or send any prompt to inspect feature extractions, token counts, and cost savings in real-time.</p>
          </div>
        )}
      </div>
    </div>
  );
};
