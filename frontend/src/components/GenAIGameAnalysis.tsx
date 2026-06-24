"use client";

import { useState, useEffect } from "react";
import { Sparkles, Bot, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface GenAIAnalysis {
  matchup?: string;
  game_date?: string;
  analysis: string;
  source: string;
  model: string;
}

export default function GenAIGameAnalysis({ gameId, defaultExpanded = false }: { gameId: number, defaultExpanded?: boolean }) {
  const [analysis, setAnalysis] = useState<GenAIAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(defaultExpanded);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/genai/game/${gameId}/analysis`);
      if (res.ok) {
        const data = await res.json();
        setAnalysis(data);
      } else {
        setError("無法生成 AI 分析");
      }
    } catch {
      setError("AI 分析服務暫時無法使用");
    }
    setLoading(false);
  };

  useEffect(() => {
    if (expanded && !analysis && !loading && !error) {
      fetchAnalysis();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expanded, gameId]);

  // Simple markdown-to-html converter for basic formatting
  const renderMarkdown = (text: string) => {
    const lines = text.split("\n");
    return lines.map((line, i) => {
      // Headers
      if (line.startsWith("### ")) {
        return <h4 key={i} className="genai-h4">{line.slice(4)}</h4>;
      }
      if (line.startsWith("## ")) {
        return <h3 key={i} className="genai-h3">{line.slice(3)}</h3>;
      }
      // Horizontal rule
      if (line.trim() === "---") {
        return <hr key={i} className="genai-hr" />;
      }
      // Empty line
      if (line.trim() === "") {
        return <div key={i} className="genai-spacer" />;
      }
      // Bold text: replace **text** with <strong>
      const parts = line.split(/\*\*(.*?)\*\*/g);
      const rendered = parts.map((part, j) => {
        if (j % 2 === 1) {
          return <strong key={j}>{part}</strong>;
        }
        return <span key={j}>{part}</span>;
      });
      // Italic (single line at end usually means footnote)
      if (line.startsWith("*") && line.endsWith("*") && !line.startsWith("**")) {
        return <p key={i} className="genai-footnote">{line.slice(1, -1)}</p>;
      }
      return <p key={i} className="genai-p">{rendered}</p>;
    });
  };

  return (
    <div className="genai-game-section glass" style={{ marginTop: '1rem', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
      <div 
        className="genai-game-header" 
        onClick={() => setExpanded(!expanded)}
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          padding: '0.75rem 1rem', 
          cursor: 'pointer',
          background: 'rgba(255,255,255,0.02)',
          borderBottom: expanded ? '1px solid rgba(255,255,255,0.05)' : 'none'
        }}
      >
        <div className="genai-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Sparkles size={16} className="genai-icon" />
          <h4 style={{ margin: 0, fontSize: '0.9rem', fontWeight: 600 }}>AI 賽前分析與攻防重點</h4>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </div>

      {expanded && (
        <div className="genai-body" style={{ padding: '1rem' }}>
          {loading && (
            <div className="genai-loading">
              <div className="genai-loading-dots">
                <span></span><span></span><span></span>
              </div>
              <p style={{ fontSize: '0.85rem' }}>AI 正在分析雙方戰力與歷史對戰...</p>
            </div>
          )}

          {error && !loading && (
            <div className="genai-error" style={{ textAlign: 'center', padding: '1rem 0' }}>
              <p style={{ fontSize: '0.85rem', color: 'var(--color-danger)' }}>⚠️ {error}</p>
              <button onClick={(e) => { e.stopPropagation(); fetchAnalysis(); }} className="genai-retry-btn" style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>重試</button>
            </div>
          )}

          {analysis && !loading && (
            <div className="genai-content" style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
              {renderMarkdown(analysis.analysis)}
              <div className="genai-model-info" style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px dashed rgba(255,255,255,0.1)', justifyContent: 'flex-start' }}>
                <Bot size={12} />
                <span style={{ fontSize: '0.75rem' }}>由 {analysis.model} ({analysis.source === "gemini" ? "Gemini" : analysis.source === "openai" ? "GPT-4o" : "規則引擎"}) 生成</span>
                <button
                  className="genai-refresh-btn"
                  onClick={(e) => { e.stopPropagation(); fetchAnalysis(); }}
                  disabled={loading}
                  title="重新生成"
                  style={{ padding: '2px', marginLeft: 'auto' }}
                >
                  <RefreshCw size={12} className={loading ? "spinning" : ""} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
