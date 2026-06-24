import Link from "next/link";
import { 
  getPlayer, 
  getPlayerBattingStats, 
  getPlayerPitchingStats, 
  getPlayerGamelog,
  Player,
  BattingStats,
  PitchingStats,
  PlayerGameLog
} from "@/lib/api";
import { ChevronLeft, Calendar, User, TrendingUp, BarChart2 } from "lucide-react";
import { notFound } from "next/navigation";
import GenAIPlayerAnalysis from "@/components/GenAIPlayerAnalysis";

export const revalidate = 5;

// Mock Fallbacks for Batting
const MOCK_BATTING: BattingStats = {
  player_name: "Mock Player", player_id: 1, at_bats: 550, runs: 95, hits: 158, doubles: 32, triples: 2, home_runs: 28, rbi: 85, walks: 72, strikeouts: 120, stolen_bases: 15, plate_appearances: 630, avg: 0.287, obp: 0.370, slg: 0.505, ops: 0.875
};

// Mock Fallbacks for Pitching
const MOCK_PITCHING: PitchingStats = {
  player_name: "Mock Pitcher", player_id: 2, innings_pitched: 175.2, hits_allowed: 148, runs_allowed: 75, earned_runs: 68, walks_allowed: 48, strikeouts: 185, home_runs_allowed: 18, pitches_thrown: 2750, era: 3.48, whip: 1.12, wins: 14, losses: 7, saves: 0
};

// Mock Fallbacks for Gamelog
const MOCK_GAMELOG: PlayerGameLog[] = [
  { game_date: "2024-09-29", opponent: "Boston Red Sox", opponent_abbr: "BOS", is_home: true, at_bats: 4, hits: 2, home_runs: 1, rbi: 2, walks: 1, strikeouts: 0, avg: 0.500 },
  { game_date: "2024-09-28", opponent: "Boston Red Sox", opponent_abbr: "BOS", is_home: true, at_bats: 3, hits: 1, home_runs: 0, rbi: 0, walks: 1, strikeouts: 1, avg: 0.333 },
  { game_date: "2024-09-27", opponent: "Boston Red Sox", opponent_abbr: "BOS", is_home: true, at_bats: 4, hits: 0, home_runs: 0, rbi: 0, walks: 0, strikeouts: 2, avg: 0.000 },
  { game_date: "2024-09-25", opponent: "Oakland Athletics", opponent_abbr: "OAK", is_home: false, at_bats: 5, hits: 3, home_runs: 2, rbi: 4, walks: 0, strikeouts: 1, avg: 0.600 },
  { game_date: "2024-09-24", opponent: "Oakland Athletics", opponent_abbr: "OAK", is_home: false, at_bats: 4, hits: 1, home_runs: 0, rbi: 1, walks: 1, strikeouts: 0, avg: 0.250 },
];

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function PlayerDetailPage({ params }: PageProps) {
  const resolvedParams = await params;
  const playerId = Number(resolvedParams.id);

  if (isNaN(playerId)) {
    notFound();
  }

  const player = await getPlayer(playerId);
  if (!player) {
    notFound();
  }

  const isPitcher = ["P", "SP", "RP", "LHP", "RHP"].includes(player.primary_position);
  
  // Fetch stats from backend
  const dbBatting = await getPlayerBattingStats(playerId);
  const dbPitching = await getPlayerPitchingStats(playerId);
  const dbGamelog = await getPlayerGamelog(playerId);

  // Fallback check: If database returns empty/null stats (records = 0), apply mock data
  const hasBattingStats = dbBatting && dbBatting.at_bats > 0;
  const hasPitchingStats = dbPitching && dbPitching.innings_pitched > 0;
  const hasGamelog = dbGamelog && dbGamelog.length > 0;

  const battingStats = hasBattingStats ? dbBatting : { ...MOCK_BATTING, player_name: player.full_name, player_id: player.id };
  const pitchingStats = hasPitchingStats ? dbPitching : { ...MOCK_PITCHING, player_name: player.full_name, player_id: player.id };
  const gamelog = hasGamelog ? dbGamelog : MOCK_GAMELOG;

  // Calculate age from birth date
  let age = null;
  if (player.birth_date) {
    const birth = new Date(player.birth_date);
    const today = new Date();
    age = today.getFullYear() - birth.getFullYear();
    const m = today.getMonth() - birth.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) {
      age--;
    }
  }

  const savantStats = player.savant_stats;

  // Gauge computations helper
  const getGaugeProps = (name: string, val: number, isPitcher: boolean) => {
    let pct = 0;
    let colorClass = "fill-neutral";
    if (name === "avg_exit_velocity") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((92 - val) / 7) * 100)); // 92mph (0%) to 85mph (100%)
        colorClass = val <= 87.0 ? "fill-red" : val <= 88.5 ? "fill-orange" : val <= 90.0 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 85) / 10) * 100)); // 85mph (0%) to 95mph (100%)
        colorClass = val >= 92.0 ? "fill-red" : val >= 89.5 ? "fill-orange" : val >= 87.0 ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "max_exit_velocity") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((114 - val) / 12) * 100)); // 114 (0%) to 102 (100%)
        colorClass = val <= 106.0 ? "fill-red" : val <= 109.0 ? "fill-orange" : val <= 111.0 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 100) / 16) * 100)); // 100 (0%) to 116 (100%)
        colorClass = val >= 112.0 ? "fill-red" : val >= 108.0 ? "fill-orange" : val >= 104.0 ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "barrel_rate") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((12 - val) / 9) * 100)); // 12% (0%) to 3% (100%)
        colorClass = val <= 5.5 ? "fill-red" : val <= 7.5 ? "fill-orange" : val <= 9.0 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 2) / 16) * 100)); // 2% (0%) to 18% (100%)
        colorClass = val >= 12.0 ? "fill-red" : val >= 8.0 ? "fill-orange" : val >= 5.0 ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "avg_launch_angle") {
      pct = Math.max(0, Math.min(100, ((val + 5) / 30) * 100)); // -5 to 25
      if (isPitcher) {
        colorClass = val <= 8.0 ? "fill-red" : val <= 12.0 ? "fill-orange" : val <= 16.0 ? "fill-neutral" : "fill-blue";
      } else {
        colorClass = (val >= 12.0 && val <= 18.0) ? "fill-red" : (val >= 8.0 && val <= 22.0) ? "fill-orange" : (val >= 4.0 && val <= 25.0) ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "xba") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((0.280 - val) / 0.080) * 100)); // .280 (0%) to .200 (100%)
        colorClass = val <= 0.220 ? "fill-red" : val <= 0.245 ? "fill-orange" : val <= 0.260 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 0.210) / 0.090) * 100)); // .210 (0%) to .300 (100%)
        colorClass = val >= 0.280 ? "fill-red" : val >= 0.255 ? "fill-orange" : val >= 0.230 ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "xslg") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((0.480 - val) / 0.160) * 100)); // .480 (0%) to .320 (100%)
        colorClass = val <= 0.360 ? "fill-red" : val <= 0.400 ? "fill-orange" : val <= 0.440 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 0.320) / 0.230) * 100)); // .320 (0%) to .550 (100%)
        colorClass = val >= 0.480 ? "fill-red" : val >= 0.420 ? "fill-orange" : val >= 0.380 ? "fill-neutral" : "fill-blue";
      }
    } else if (name === "xwoba") {
      if (isPitcher) {
        pct = Math.max(0, Math.min(100, ((0.360 - val) / 0.100) * 100)); // .360 (0%) to .260 (100%)
        colorClass = val <= 0.290 ? "fill-red" : val <= 0.315 ? "fill-orange" : val <= 0.335 ? "fill-neutral" : "fill-blue";
      } else {
        pct = Math.max(0, Math.min(100, ((val - 0.260) / 0.120) * 100)); // .260 (0%) to .380 (100%)
        colorClass = val >= 0.350 ? "fill-red" : val >= 0.320 ? "fill-orange" : val >= 0.290 ? "fill-neutral" : "fill-blue";
      }
    }
    return { pct: Math.round(pct), colorClass };
  };

  return (
    <div className="player-detail-container animate-fade-in">
      {/* Back Button */}
      <div className="back-nav">
        {player.team ? (
          <Link href={`/teams/${player.team.id}`} className="back-link">
            <ChevronLeft size={16} /> <span>返回 {player.team.name} 名冊</span>
          </Link>
        ) : (
          <Link href="/players" className="back-link">
            <ChevronLeft size={16} /> <span>返回球員目錄</span>
          </Link>
        )}
      </div>

      {/* Player Profile Header Card */}
      <section className="player-hero glass">
        <div className="player-avatar-large">
          <img src={player.headshot_url} alt={player.full_name} />
          {player.jersey_number && (
            <span className="jersey-badge">#{player.jersey_number}</span>
          )}
        </div>

        <div className="player-title-info">
          <div className="team-position-breadcrumbs">
            {player.team && (
              <>
                <Link href={`/teams/${player.team.id}`} className="team-link">
                  {player.team.name}
                </Link>
                <span className="dot">•</span>
              </>
            )}
            <span>{player.primary_position}</span>
          </div>
          <h1>{player.full_name}</h1>

          {/* Quick Bio Info */}
          <div className="bio-grid">
            <div className="bio-item">
              <span className="label">年齡</span>
              <span className="value">{age ? `${age} 歲` : "—"}</span>
            </div>
            <div className="bio-item">
              <span className="label">身高 / 體重</span>
              <span className="value">
                {player.height ? player.height : "—"} / {player.weight ? `${player.weight} lbs` : "—"}
              </span>
            </div>
            <div className="bio-item">
              <span className="label">投 / 打</span>
              <span className="value">{player.throws} 投 / {player.bats} 打</span>
            </div>
            <div className="bio-item">
              <span className="label">國籍</span>
              <span className="value">{player.birth_country || "—"}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Statcast Advanced Metrics Section */}
      <section className="stats-section glass" style={{ marginBottom: "0rem" }}>
        <div className="section-header">
          <div className="section-title">
            <TrendingUp size={20} color="var(--color-accent)" />
            <h2>Statcast 進階數據分析 (2024)</h2>
          </div>
          {savantStats ? (
            <span className="demo-indicator" style={{ backgroundColor: "rgba(255, 59, 48, 0.12)", color: "var(--color-accent)" }}>
              Statcast 官方數據
            </span>
          ) : (
            <span className="demo-indicator" style={{ backgroundColor: "rgba(255, 255, 255, 0.1)", color: "var(--text-muted)" }}>
              暫無進階數據
            </span>
          )}
        </div>

        {savantStats ? (
          <div className="statcast-container">
            <div className="statcast-grid">
              {/* Avg Exit Velocity */}
              {savantStats.avg_exit_velocity !== null && (() => {
                const { pct, colorClass } = getGaugeProps("avg_exit_velocity", savantStats.avg_exit_velocity, isPitcher);
                return (
                  <div className="statcast-metric-card" key="avg-ev">
                    <span className="statcast-label">平均擊球速 (Avg EV)</span>
                    <span className="statcast-value">{savantStats.avg_exit_velocity} <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>mph</span></span>
                    <div className="statcast-bar-container">
                      <div className={`statcast-bar-fill ${colorClass}`} style={{ width: `${pct}%` }}></div>
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                      擊球強度分位值: {pct}%
                    </span>
                  </div>
                );
              })()}

              {/* Max Exit Velocity */}
              {savantStats.max_exit_velocity !== null && (() => {
                const { pct, colorClass } = getGaugeProps("max_exit_velocity", savantStats.max_exit_velocity, isPitcher);
                return (
                  <div className="statcast-metric-card" key="max-ev">
                    <span className="statcast-label">最大擊球速 (Max EV)</span>
                    <span className="statcast-value">{savantStats.max_exit_velocity} <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>mph</span></span>
                    <div className="statcast-bar-container">
                      <div className={`statcast-bar-fill ${colorClass}`} style={{ width: `${pct}%` }}></div>
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                      爆發力分位值: {pct}%
                    </span>
                  </div>
                );
              })()}

              {/* Barrel Rate */}
              {savantStats.barrel_rate !== null && (() => {
                const { pct, colorClass } = getGaugeProps("barrel_rate", savantStats.barrel_rate, isPitcher);
                return (
                  <div className="statcast-metric-card" key="barrel-rate">
                    <span className="statcast-label">出色擊球率 (Barrel%)</span>
                    <span className="statcast-value">{savantStats.barrel_rate} <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>%</span></span>
                    <div className="statcast-bar-container">
                      <div className={`statcast-bar-fill ${colorClass}`} style={{ width: `${pct}%` }}></div>
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                      出色擊球分位值: {pct}%
                    </span>
                  </div>
                );
              })()}

              {/* Launch Angle */}
              {savantStats.avg_launch_angle !== null && (() => {
                const { pct, colorClass } = getGaugeProps("avg_launch_angle", savantStats.avg_launch_angle, isPitcher);
                return (
                  <div className="statcast-metric-card" key="launch-angle">
                    <span className="statcast-label">平均擊球仰角 (Avg LA)</span>
                    <span className="statcast-value">{savantStats.avg_launch_angle} <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>°</span></span>
                    <div className="statcast-bar-container">
                      <div className={`statcast-bar-fill ${colorClass}`} style={{ width: `${pct}%` }}></div>
                    </div>
                    <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                      仰角分布分位值: {pct}%
                    </span>
                  </div>
                );
              })()}
            </div>

            {/* Expected vs Actual stats comparison */}
            <div className="expected-stats-comparison">
              <h3>
                <BarChart2 size={16} color="var(--color-primary)" />
                <span>期望數據 vs. 實際數據對比 (Expected vs. Actual)</span>
              </h3>
              <div className="comparison-grid">
                {isPitcher ? (
                  <>
                    <div className="comparison-row pitcher">
                      <span className="comparison-label">期望被打擊率 (xBA)</span>
                      <div className="comparison-values">
                        <div className="comparison-value-item">
                          <span className="val">.{Math.round((savantStats.xba || 0) * 1000)}</span>
                          <span className="lbl">Expected</span>
                        </div>
                        <div className="comparison-value-item">
                          <span className="val" style={{ color: "var(--text-secondary)" }}>.244</span>
                          <span className="lbl">League Avg</span>
                        </div>
                      </div>
                    </div>
                    <div className="comparison-row pitcher">
                      <span className="comparison-label">期望加權上壘率 (xwOBA)</span>
                      <div className="comparison-values">
                        <div className="comparison-value-item">
                          <span className="val">.{Math.round((savantStats.xwoba || 0) * 1000)}</span>
                          <span className="lbl">Expected</span>
                        </div>
                        <div className="comparison-value-item">
                          <span className="val" style={{ color: "var(--text-secondary)" }}>.312</span>
                          <span className="lbl">League Avg</span>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    {/* xBA vs AVG */}
                    {savantStats.xba !== null && (
                      <div className="comparison-row">
                        <span className="comparison-label">擊球率 (xBA vs AVG)</span>
                        <div className="comparison-values">
                          <div className="comparison-value-item">
                            <span className="val">.{Math.round(savantStats.xba * 1000)}</span>
                            <span className="lbl">Expected xBA</span>
                          </div>
                          <div className="comparison-value-item">
                            <span className="val">.{Math.round(battingStats.avg * 1000)}</span>
                            <span className="lbl">Actual AVG</span>
                          </div>
                          {(() => {
                            const diff = battingStats.avg - savantStats.xba;
                            const isLucky = diff > 0.015;
                            const isUnlucky = diff < -0.015;
                            return (
                              <span className={`comparison-diff ${isLucky ? "positive" : isUnlucky ? "negative" : "equal"}`}>
                                {diff > 0 ? `+${Math.round(diff * 1000)}` : `${Math.round(diff * 1000)}`}
                              </span>
                            );
                          })()}
                        </div>
                      </div>
                    )}

                    {/* xSLG vs SLG */}
                    {savantStats.xslg !== null && (
                      <div className="comparison-row">
                        <span className="comparison-label">長打率 (xSLG vs SLG)</span>
                        <div className="comparison-values">
                          <div className="comparison-value-item">
                            <span className="val">.{Math.round(savantStats.xslg * 1000)}</span>
                            <span className="lbl">Expected xSLG</span>
                          </div>
                          <div className="comparison-value-item">
                            <span className="val">.{Math.round(battingStats.slg * 1000)}</span>
                            <span className="lbl">Actual SLG</span>
                          </div>
                          {(() => {
                            const diff = battingStats.slg - savantStats.xslg;
                            const isLucky = diff > 0.03;
                            const isUnlucky = diff < -0.03;
                            return (
                              <span className={`comparison-diff ${isLucky ? "positive" : isUnlucky ? "negative" : "equal"}`}>
                                {diff > 0 ? `+${Math.round(diff * 1000)}` : `${Math.round(diff * 1000)}`}
                              </span>
                            );
                          })()}
                        </div>
                      </div>
                    )}

                    {/* xwOBA vs League wOBA */}
                    {savantStats.xwoba !== null && (
                      <div className="comparison-row">
                        <span className="comparison-label">加權上壘率 (xwOBA vs League)</span>
                        <div className="comparison-values">
                          <div className="comparison-value-item">
                            <span className="val">.{Math.round(savantStats.xwoba * 1000)}</span>
                            <span className="lbl">Expected xwOBA</span>
                          </div>
                          <div className="comparison-value-item">
                            <span className="val" style={{ color: "var(--text-secondary)" }}>.312</span>
                            <span className="lbl">League Avg</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="no-data-prompt" style={{ padding: "3rem", textAlign: "center", color: "var(--text-muted)", background: "rgba(255,255,255,0.02)", borderRadius: "var(--radius-md)" }}>
            <TrendingUp size={32} style={{ opacity: 0.3, marginBottom: "1rem" }} />
            <p>目前資料庫尚無該球員的 Statcast 官方進階數據。</p>
          </div>
        )}
      </section>

      {/* Main stats panels */}
      <div className="stats-layout-grid">
        
        {/* Batting/Pitching stats dashboard */}
        <section className="stats-section glass">
          <div className="section-header">
            <div className="section-title">
              <BarChart2 size={20} color="var(--color-primary)" />
              <h2>2024 Regular Season 數據摘要</h2>
            </div>
            {!hasBattingStats && !hasPitchingStats && (
              <span className="demo-indicator">模擬數據 (等待背景同步)</span>
            )}
          </div>

          {isPitcher ? (
            /* Pitcher View */
            <div className="stats-dashboard">
              <div className="primary-stats-grid">
                <div className="metric-box">
                  <span className="num text-gradient">{pitchingStats.era.toFixed(2)}</span>
                  <span className="label">防禦率 (ERA)</span>
                </div>
                <div className="metric-box">
                  <span className="num">{pitchingStats.wins} - {pitchingStats.losses}</span>
                  <span className="label">勝 - 敗</span>
                </div>
                <div className="metric-box">
                  <span className="num">{pitchingStats.strikeouts}</span>
                  <span className="label">三振數 (SO)</span>
                </div>
                <div className="metric-box">
                  <span className="num">{pitchingStats.whip.toFixed(2)}</span>
                  <span className="label">每局被上壘率 (WHIP)</span>
                </div>
              </div>

              <div className="secondary-stats-list">
                <div className="stat-row">
                  <span>投球局數 (Innings Pitched)</span>
                  <span className="val">{pitchingStats.innings_pitched.toFixed(1)} IP</span>
                </div>
                <div className="stat-row">
                  <span>被安打數 (Hits Allowed)</span>
                  <span className="val">{pitchingStats.hits_allowed} H</span>
                </div>
                <div className="stat-row">
                  <span>四壞保送 (Walks Allowed)</span>
                  <span className="val">{pitchingStats.walks_allowed} BB</span>
                </div>
                <div className="stat-row">
                  <span>失分 / 自責分</span>
                  <span className="val">{pitchingStats.runs_allowed} / {pitchingStats.earned_runs}</span>
                </div>
                <div className="stat-row">
                  <span>被全壘打 (HR Allowed)</span>
                  <span className="val">{pitchingStats.home_runs_allowed} HR</span>
                </div>
                <div className="stat-row">
                  <span>救援成功 (Saves)</span>
                  <span className="val">{pitchingStats.saves} SV</span>
                </div>
              </div>
            </div>
          ) : (
            /* Batter/Position Player View */
            <div className="stats-dashboard">
              <div className="primary-stats-grid">
                <div className="metric-box">
                  <span className="num text-gradient">.{Math.round(battingStats.avg * 1000)}</span>
                  <span className="label">打擊率 (AVG)</span>
                </div>
                <div className="metric-box">
                  <span className="num">{battingStats.home_runs}</span>
                  <span className="label">全壘打 (HR)</span>
                </div>
                <div className="metric-box">
                  <span className="num">{battingStats.rbi}</span>
                  <span className="label">打點 (RBI)</span>
                </div>
                <div className="metric-box">
                  <span className="num">.{Math.round(battingStats.ops * 1000)}</span>
                  <span className="label">攻擊指數 (OPS)</span>
                </div>
              </div>

              <div className="secondary-stats-list">
                <div className="stat-row">
                  <span>上壘率 (OBP) / 長打率 (SLG)</span>
                  <span className="val">.{Math.round(battingStats.obp * 1000)} / .{Math.round(battingStats.slg * 1000)}</span>
                </div>
                <div className="stat-row">
                  <span>打席數 (PA) / 打數 (AB)</span>
                  <span className="val">{battingStats.plate_appearances} / {battingStats.at_bats}</span>
                </div>
                <div className="stat-row">
                  <span>安打數 (Hits)</span>
                  <span className="val">{battingStats.hits} H (二壘打 {battingStats.doubles} / 三壘打 {battingStats.triples})</span>
                </div>
                <div className="stat-row">
                  <span>保送 (BB) / 三振 (SO)</span>
                  <span className="val">{battingStats.walks} BB / {battingStats.strikeouts} SO</span>
                </div>
                <div className="stat-row">
                  <span>得分 (Runs)</span>
                  <span className="val">{battingStats.runs} R</span>
                </div>
                <div className="stat-row">
                  <span>盜壘成功 (Stolen Bases)</span>
                  <span className="val">{battingStats.stolen_bases} SB</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* GenAI Analysis Section */}
        <GenAIPlayerAnalysis playerId={player.id} />

        {/* Recent Game Log Table */}
        <section className="stats-section glass">
          <div className="section-header">
            <div className="section-title">
              <Calendar size={20} color="var(--color-secondary)" />
              <h2>近期比賽日誌 (Recent Games)</h2>
            </div>
            {!hasGamelog && (
              <span className="demo-indicator">模擬日誌 (等待背景同步)</span>
            )}
          </div>

          <div className="table-responsive">
            <table className="gamelog-table">
              <thead>
                {isPitcher ? (
                  /* Pitcher Column Headers */
                  <tr>
                    <th>日期</th>
                    <th>對手</th>
                    <th>主/客</th>
                    <th className="th-num">投球局</th>
                    <th className="th-num">被安打</th>
                    <th className="th-num">失分</th>
                    <th className="th-num">自責分</th>
                    <th className="th-num">奪三振</th>
                  </tr>
                ) : (
                  /* Batter Column Headers */
                  <tr>
                    <th>日期</th>
                    <th>對手</th>
                    <th>主/客</th>
                    <th className="th-num">打數</th>
                    <th className="th-num">安打</th>
                    <th className="th-num">全壘打</th>
                    <th className="th-num">打點</th>
                    <th className="th-num">保送</th>
                    <th className="th-num">單場AVG</th>
                  </tr>
                )}
              </thead>
              <tbody>
                {gamelog.map((log, idx) => (
                  <tr key={idx} className="gamelog-row">
                    <td>{log.game_date.substring(5)}</td>
                    <td>
                      <span className="opp-abbr">{log.opponent_abbr}</span>
                      <span className="opp-fullname">{log.opponent}</span>
                    </td>
                    <td>{log.is_home ? "主場" : "客場"}</td>
                    {isPitcher ? (
                      /* Pitcher Gamelog Values */
                      <>
                        <td className="td-num font-medium">{log.innings_pitched != null ? log.innings_pitched.toFixed(1) : "—"}</td>
                        <td className="td-num">{log.hits_allowed ?? "—"}</td>
                        <td className="td-num text-muted">{log.runs_allowed ?? "—"}</td>
                        <td className="td-num text-secondary font-bold">{log.earned_runs ?? "—"}</td>
                        <td className="td-num font-semibold">{log.pitching_strikeouts ?? "—"}</td>
                      </>
                    ) : (
                      /* Batter Gamelog Values */
                      <>
                        <td className="td-num font-medium">{log.at_bats ?? 0}</td>
                        <td className="td-num font-medium">{log.hits ?? 0}</td>
                        <td className="td-num text-secondary font-bold">
                          {(log.home_runs ?? 0) > 0 ? log.home_runs : "—"}
                        </td>
                        <td className="td-num">{log.rbi ?? 0}</td>
                        <td className="td-num text-muted">{log.walks ?? 0}</td>
                        <td className="td-num font-semibold text-secondary">
                          {(log.hits ?? 0) > 0 ? `.${Math.round(((log.hits ?? 0) / (log.at_bats || 1)) * 1000)}` : ".000"}
                        </td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}
