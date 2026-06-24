"use client";

import { useState, useEffect } from "react";
import { Sparkles, Bot, RefreshCw } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

interface GenAIAnalysis {
  player_name?: string;
  analysis: string;
  source: string;
  model: string;
}

export default function GenAIPlayerAnalysis({ playerId }: { playerId: number }) {
  const [analysis, setAnalysis] = useState<GenAIAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/genai/player/${playerId}/analysis`);
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
    fetchAnalysis();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playerId]);

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
    <div className="genai-section glass animate-fade-in">
      <div className="genai-header">
        <div className="genai-title">
          <Sparkles size={20} className="genai-icon" />
          <h3>AI 智慧分析</h3>
          <span className="genai-badge">
            <Bot size={12} />
            {analysis?.source === "rule_based" ? "AI 規則引擎" :
             analysis?.source === "gemini" ? "Gemini AI" :
             analysis?.source === "openai" ? "GPT-4o" : "AI"}
          </span>
        </div>
        <button
          className="genai-refresh-btn"
          onClick={fetchAnalysis}
          disabled={loading}
          title="重新生成分析"
        >
          <RefreshCw size={16} className={loading ? "spinning" : ""} />
        </button>
      </div>

      <div className="genai-body">
        {loading && (
          <div className="genai-loading">
            <div className="genai-loading-dots">
              <span></span><span></span><span></span>
            </div>
            <p>AI 正在分析球員數據...</p>
          </div>
        )}

        {error && !loading && (
          <div className="genai-error">
            <p>⚠️ {error}</p>
            <button onClick={fetchAnalysis} className="genai-retry-btn">重試</button>
          </div>
        )}

        {analysis && !loading && (
          <div className="genai-content">
            {renderMarkdown(analysis.analysis)}
            <div className="genai-model-info">
              <Bot size={14} />
              <span>由 {analysis.model} 生成</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
