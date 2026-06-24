"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { BarChart3, ChevronUp, ChevronDown, Filter, ChevronLeft, ChevronRight } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// ─── Type definitions ───
interface BattingRow {
  rank: number;
  player_id: number;
  player_name: string;
  position: string;
  headshot_url: string;
  team: string;
  pa: number; ab: number; h: number; doubles: number; triples: number;
  home_runs: number; runs: number; rbi: number; walks: number;
  strikeouts: number; stolen_bases: number; caught_stealing: number;
  avg: number; obp: number; slg: number; ops: number;
}

interface PitchingRow {
  rank: number;
  player_id: number;
  player_name: string;
  position: string;
  headshot_url: string;
  team: string;
  ip: number; h: number; r: number; er: number; bb: number;
  strikeouts: number; hr: number; wins: number; losses: number;
  saves: number; holds: number; games: number; games_started: number;
  era: number; whip: number; k9: number; bb9: number;
}

interface SavantRow {
  rank: number;
  player_id: number;
  player_name: string;
  position: string;
  headshot_url: string;
  team: string;
  avg_exit_velocity: number;
  max_exit_velocity: number;
  avg_launch_angle: number;
  barrel_rate: number;
  xba: number;
  xslg: number;
  xwoba: number;
}

interface PagedResponse<T> {
  total: number;
  page: number;
  per_page: number;
  data: T[];
}

// ─── Column definitions ───
const BATTING_COLUMNS = [
  { key: "rank", label: "#", sortable: false, width: "50px" },
  { key: "player_name", label: "球員", sortable: false, width: "200px" },
  { key: "team", label: "球隊", sortable: false, width: "60px" },
  { key: "position", label: "位置", sortable: false, width: "50px" },
  { key: "pa", label: "PA", sortable: true, width: "55px", tip: "打席數" },
  { key: "ab", label: "AB", sortable: true, width: "55px", tip: "打數" },
  { key: "h", label: "H", sortable: true, width: "50px", tip: "安打" },
  { key: "doubles", label: "2B", sortable: true, width: "45px", tip: "二壘安打" },
  { key: "triples", label: "3B", sortable: true, width: "45px", tip: "三壘安打" },
  { key: "home_runs", label: "HR", sortable: true, width: "50px", tip: "全壘打" },
  { key: "runs", label: "R", sortable: true, width: "50px", tip: "得分" },
  { key: "rbi", label: "RBI", sortable: true, width: "50px", tip: "打點" },
  { key: "walks", label: "BB", sortable: true, width: "50px", tip: "四壞球" },
  { key: "strikeouts", label: "K", sortable: true, width: "50px", tip: "三振" },
  { key: "stolen_bases", label: "SB", sortable: true, width: "50px", tip: "盜壘" },
  { key: "avg", label: "AVG", sortable: true, width: "60px", tip: "打擊率" },
  { key: "obp", label: "OBP", sortable: true, width: "60px", tip: "上壘率" },
  { key: "slg", label: "SLG", sortable: true, width: "60px", tip: "長打率" },
  { key: "ops", label: "OPS", sortable: true, width: "65px", tip: "整體攻擊力" },
];

const PITCHING_COLUMNS = [
  { key: "rank", label: "#", sortable: false, width: "50px" },
  { key: "player_name", label: "球員", sortable: false, width: "200px" },
  { key: "team", label: "球隊", sortable: false, width: "60px" },
  { key: "wins", label: "W", sortable: true, width: "45px", tip: "勝場" },
  { key: "losses", label: "L", sortable: false, width: "45px", tip: "敗場" },
  { key: "era", label: "ERA", sortable: true, width: "60px", tip: "自責分率" },
  { key: "games", label: "G", sortable: false, width: "45px", tip: "出賽" },
  { key: "games_started", label: "GS", sortable: false, width: "45px", tip: "先發" },
  { key: "ip", label: "IP", sortable: true, width: "60px", tip: "投球局數" },
  { key: "h", label: "H", sortable: false, width: "50px", tip: "被安打" },
  { key: "er", label: "ER", sortable: false, width: "50px", tip: "自責分" },
  { key: "bb", label: "BB", sortable: false, width: "50px", tip: "四壞球" },
  { key: "strikeouts", label: "K", sortable: true, width: "50px", tip: "三振" },
  { key: "hr", label: "HR", sortable: true, width: "50px", tip: "被全壘打" },
  { key: "saves", label: "SV", sortable: true, width: "50px", tip: "救援成功" },
  { key: "holds", label: "HLD", sortable: true, width: "50px", tip: "中繼成功" },
  { key: "whip", label: "WHIP", sortable: true, width: "65px", tip: "每局上壘率" },
  { key: "k9", label: "K/9", sortable: true, width: "55px", tip: "每9局三振" },
  { key: "bb9", label: "BB/9", sortable: true, width: "55px", tip: "每9局四壞" },
];

const SAVANT_COLUMNS = [
  { key: "rank", label: "#", sortable: false, width: "50px" },
  { key: "player_name", label: "球員", sortable: false, width: "200px" },
  { key: "team", label: "球隊", sortable: false, width: "60px" },
  { key: "avg_exit_velocity", label: "Avg EV", sortable: true, width: "80px", tip: "平均擊球初速" },
  { key: "max_exit_velocity", label: "Max EV", sortable: true, width: "80px", tip: "最大擊球初速" },
  { key: "avg_launch_angle", label: "LA", sortable: true, width: "60px", tip: "平均擊球仰角" },
  { key: "barrel_rate", label: "Barrel%", sortable: true, width: "80px", tip: "桶子率(優質擊球)" },
  { key: "xba", label: "xBA", sortable: true, width: "70px", tip: "預期打擊率" },
  { key: "xslg", label: "xSLG", sortable: true, width: "70px", tip: "預期長打率" },
  { key: "xwoba", label: "xwOBA", sortable: true, width: "80px", tip: "預期加權上壘率" },
];

const TEAMS = [
  "AZ","ATL","BAL","BOS","CHC","CIN","CLE","COL","CWS","DET",
  "HOU","KC","LAA","LAD","MIA","MIL","MIN","NYM","NYY","OAK",
  "PHI","PIT","SD","SF","SEA","STL","TB","TEX","TOR","WSH"
];

const POSITIONS = ["C","1B","2B","3B","SS","LF","CF","RF","DH","P"];

const MIN_PA_OPTIONS = [0, 50, 100, 200, 300, 400, 502];
const MIN_IP_OPTIONS = [0, 10, 30, 50, 100, 162];
const PER_PAGE_OPTIONS = [25, 50, 100];

export default function LeaderboardPage() {
  const [tab, setTab] = useState<"batting" | "pitching" | "savant">("batting");
  const [battingData, setBattingData] = useState<PagedResponse<BattingRow> | null>(null);
  const [pitchingData, setPitchingData] = useState<PagedResponse<PitchingRow> | null>(null);
  const [savantData, setSavantData] = useState<PagedResponse<SavantRow> | null>(null);
  const [loading, setLoading] = useState(true);

  // Filters
  const [sortBy, setSortBy] = useState("home_runs");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");
  const [minPA, setMinPA] = useState(50);
  const [minIP, setMinIP] = useState(10);
  const [perPage, setPerPage] = useState(50);
  const [page, setPage] = useState(1);
  const [teamFilter, setTeamFilter] = useState("");
  const [posFilter, setPosFilter] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      if (tab === "batting") {
        const params = new URLSearchParams({
          sort: sortBy,
          order: sortOrder,
          min_pa: minPA.toString(),
          limit: perPage.toString(),
          page: page.toString(),
        });
        if (teamFilter) params.set("team", teamFilter);
        if (posFilter) params.set("position", posFilter);

        const res = await fetch(`${API_BASE}/api/analysis/leaderboard/batting?${params}`);
        if (res.ok) setBattingData(await res.json());
      } else if (tab === "pitching") {
        const params = new URLSearchParams({
          sort: sortBy,
          order: sortOrder,
          min_ip: minIP.toString(),
          limit: perPage.toString(),
          page: page.toString(),
        });
        if (teamFilter) params.set("team", teamFilter);

        const res = await fetch(`${API_BASE}/api/analysis/leaderboard/pitching?${params}`);
        if (res.ok) setPitchingData(await res.json());
      } else if (tab === "savant") {
        const params = new URLSearchParams({
          sort: sortBy,
          order: sortOrder,
          limit: perPage.toString(),
          page: page.toString(),
        });
        if (teamFilter) params.set("team", teamFilter);
        // We only fetch batters for savant leaderboard currently (is_pitcher=false)
        const res = await fetch(`${API_BASE}/api/analysis/leaderboard/savant?is_pitcher=false&${params}`);
        if (res.ok) setSavantData(await res.json());
      }
    } catch (err) {
      console.error("Leaderboard fetch error:", err);
    }
    setLoading(false);
  }, [tab, sortBy, sortOrder, minPA, minIP, perPage, page, teamFilter, posFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // When switching tabs, reset sort to defaults
  const switchTab = (newTab: "batting" | "pitching" | "savant") => {
    setTab(newTab);
    setPage(1);
    if (newTab === "batting") setSortBy("home_runs");
    else if (newTab === "pitching") setSortBy("strikeouts");
    else setSortBy("avg_exit_velocity");
    setSortOrder("desc");
    setPosFilter("");
  };

  const handleSort = (key: string) => {
    if (key === sortBy) {
      setSortOrder(prev => prev === "desc" ? "asc" : "desc");
    } else {
      setSortBy(key);
      // Rate stats should default to desc except ERA/WHIP/BB9
      if (["era", "whip", "bb9"].includes(key)) {
        setSortOrder("asc");
      } else {
        setSortOrder("desc");
      }
    }
    setPage(1);
  };

  const currentData = tab === "batting" ? battingData : tab === "pitching" ? pitchingData : savantData;
  const totalPages = currentData ? Math.ceil(currentData.total / perPage) : 1;
  const columns = tab === "batting" ? BATTING_COLUMNS : tab === "pitching" ? PITCHING_COLUMNS : SAVANT_COLUMNS;

  const formatValue = (key: string, value: unknown) => {
    if (value === null || value === undefined) return "—";
    if (["avg", "obp", "slg", "ops"].includes(key)) {
      return (value as number).toFixed(3);
    }
    if (["era", "whip"].includes(key)) {
      return (value as number).toFixed(2);
    }
    if (["k9", "bb9"].includes(key)) {
      return (value as number).toFixed(1);
    }
    if (["avg_exit_velocity", "max_exit_velocity", "avg_launch_angle", "barrel_rate"].includes(key)) {
      return (value as number).toFixed(1);
    }
    if (["xba", "xslg", "xwoba"].includes(key)) {
      return (value as number).toFixed(3);
    }
    if (key === "ip") {
      return (value as number).toFixed(1);
    }
    return String(value);
  };

  return (
    <div className="leaderboard-container animate-fade-in">
      <header className="leaderboard-header">
        <div>
          <h1>
            <BarChart3 size={28} className="inline-icon" />
            MLB 數據排行榜
          </h1>
          <p>2024 賽季打擊與投球完整數據排行，支援篩選與排序</p>
        </div>
      </header>

      {/* Tab Switcher */}
      <div className="lb-tabs">
        <button
          className={`lb-tab ${tab === "batting" ? "active" : ""}`}
          onClick={() => switchTab("batting")}
        >
          ⚾ 打擊排行
        </button>
        <button
          className={`lb-tab ${tab === "pitching" ? "active" : ""}`}
          onClick={() => switchTab("pitching")}
        >
          🔥 投球排行
        </button>
        <button
          className={`lb-tab ${tab === "savant" ? "active" : ""}`}
          onClick={() => switchTab("savant")}
        >
          🚀 Savant 進階
        </button>
      </div>

      {/* Filters Bar */}
      <div className="lb-filters-bar glass">
        <button className="lb-filter-toggle" onClick={() => setShowFilters(!showFilters)}>
          <Filter size={16} />
          篩選條件
          {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        <div className="lb-quick-filters">
          <label>
            每頁
            <select value={perPage} onChange={(e) => { setPerPage(Number(e.target.value)); setPage(1); }}>
              {PER_PAGE_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
          <span className="lb-total-badge">
            共 {currentData?.total ?? 0} 位球員
          </span>
        </div>
      </div>

      {showFilters && (
        <div className="lb-filters-panel glass animate-fade-in">
          <div className="lb-filter-group">
            <label>
              球隊
              <select value={teamFilter} onChange={(e) => { setTeamFilter(e.target.value); setPage(1); }}>
                <option value="">全部球隊</option>
                {TEAMS.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </label>

            {tab === "batting" && (
              <label>
                守位
                <select value={posFilter} onChange={(e) => { setPosFilter(e.target.value); setPage(1); }}>
                  <option value="">全部位置</option>
                  {POSITIONS.map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </label>
            )}

            {tab === "batting" && (
              <label>
                最低打席 (PA)
                <select value={minPA} onChange={(e) => { setMinPA(Number(e.target.value)); setPage(1); }}>
                  {MIN_PA_OPTIONS.map(n => (
                    <option key={n} value={n}>{n === 502 ? "502 (合格)" : n}</option>
                  ))}
                </select>
              </label>
            )}
            
            {tab === "pitching" && (
              <label>
                最低投球局 (IP)
                <select value={minIP} onChange={(e) => { setMinIP(Number(e.target.value)); setPage(1); }}>
                  {MIN_IP_OPTIONS.map(n => (
                    <option key={n} value={n}>{n === 162 ? "162 (合格)" : n}</option>
                  ))}
                </select>
              </label>
            )}
          </div>
        </div>
      )}

      {/* Data Table */}
      <div className="lb-table-wrapper glass">
        <div className="lb-table-scroll">
          <table className="lb-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th
                    key={col.key}
                    className={`${col.sortable ? "sortable" : ""} ${sortBy === col.key ? "sorted" : ""}`}
                    style={{ width: col.width, minWidth: col.width }}
                    onClick={() => col.sortable && handleSort(col.key)}
                    title={col.tip || col.label}
                  >
                    <span className="th-content">
                      {col.label}
                      {col.sortable && sortBy === col.key && (
                        <span className="sort-arrow">
                          {sortOrder === "desc" ? "▼" : "▲"}
                        </span>
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={columns.length} className="lb-loading">
                    <div className="lb-spinner" />
                    載入中...
                  </td>
                </tr>
              ) : (currentData?.data ?? []).length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="lb-empty">
                    沒有符合條件的數據
                  </td>
                </tr>
              ) : (
                (currentData?.data ?? []).map((row: any) => (
                  <tr key={row.player_id as number} className="lb-row">
                    {columns.map(col => (
                      <td
                        key={col.key}
                        className={`${sortBy === col.key ? "sorted-col" : ""} ${col.key === "player_name" ? "td-player" : "td-stat"}`}
                      >
                        {col.key === "rank" ? (
                          <span className={`lb-rank ${(row.rank as number) <= 3 ? `lb-rank-${row.rank}` : ""}`}>
                            {row.rank as number}
                          </span>
                        ) : col.key === "player_name" ? (
                          <Link href={`/players/${row.player_id}`} className="lb-player-link">
                            <img
                              src={row.headshot_url as string}
                              alt={row.player_name as string}
                              className="lb-headshot"
                              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                            />
                            <span>{row.player_name as string}</span>
                          </Link>
                        ) : (
                          <span className={["avg","obp","slg","ops","era","whip","k9","bb9","xba","xslg","xwoba"].includes(col.key) ? "rate-stat" : ""}>
                            {formatValue(col.key, row[col.key])}
                          </span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="lb-pagination">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
            className="lb-page-btn"
          >
            <ChevronLeft size={16} /> 上一頁
          </button>
          <span className="lb-page-info">
            第 {page} / {totalPages} 頁
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
            className="lb-page-btn"
          >
            下一頁 <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
