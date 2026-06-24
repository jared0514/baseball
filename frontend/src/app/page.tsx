import Link from "next/link";
import { 
  getSummary, 
  getBattingLeaders, 
  getPitchingLeaders, 
  getSavantLeaders,
  getGames,
  BattingLeader,
  PitchingLeader,
  SavantLeader,
  GameListItem
} from "@/lib/api";
import { 
  Users, 
  Calendar, 
  Trophy, 
  Activity,
  ArrowRight,
  TrendingUp,
  Database
} from "lucide-react";

// Fallback Mock Data for 2024 Leaderboards to ensure the page is beautiful
// while the data pipeline completes its sync.
const MOCK_BATTING_LEADERS: BattingLeader[] = [
  { rank: 1, player_id: 1, player_name: "Aaron Judge", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592450/headshot/67/current", team: "NYY", value: 58, avg: 0.322 },
  { rank: 2, player_id: 2, player_name: "Shohei Ohtani", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/660271/headshot/67/current", team: "LAD", value: 54, avg: 0.310 },
  { rank: 3, player_id: 3, player_name: "Anthony Santander", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/623993/headshot/67/current", team: "BAL", value: 44, avg: 0.235 },
  { rank: 4, player_id: 4, player_name: "Juan Soto", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/665742/headshot/67/current", team: "NYY", value: 41, avg: 0.288 },
  { rank: 5, player_id: 5, player_name: "Marcell Ozuna", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/542303/headshot/67/current", team: "ATL", value: 39, avg: 0.302 }
];

const MOCK_PITCHING_LEADERS: PitchingLeader[] = [
  { rank: 1, player_id: 6, player_name: "Tarik Skubal", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/669373/headshot/67/current", team: "DET", value: 228, era: 2.39 },
  { rank: 2, player_id: 7, player_name: "Chris Sale", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/519244/headshot/67/current", team: "ATL", value: 225, era: 2.38 },
  { rank: 3, player_id: 8, player_name: "Cole Ragans", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/666142/headshot/67/current", team: "KC", value: 223, era: 3.14 },
  { rank: 4, player_id: 9, player_name: "Dylan Cease", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/656302/headshot/67/current", team: "SD", value: 224, era: 3.47 },
  { rank: 5, player_id: 10, player_name: "Zack Wheeler", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/554430/headshot/67/current", team: "PHI", value: 224, era: 2.57 }
];

const MOCK_SAVANT_EV_LEADERS: SavantLeader[] = [
  { rank: 1, player_id: 1, player_name: "Aaron Judge", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592450/headshot/67/current", team: "NYY", value: 97.0 },
  { rank: 2, player_id: 11, player_name: "Oneil Cruz", position: "SS", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/665922/headshot/67/current", team: "PIT", value: 95.8 },
  { rank: 3, player_id: 2, player_name: "Shohei Ohtani", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/660271/headshot/67/current", team: "LAD", value: 95.8 },
  { rank: 4, player_id: 12, player_name: "Giancarlo Stanton", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/519317/headshot/67/current", team: "NYY", value: 95.1 },
  { rank: 5, player_id: 13, player_name: "Matt Chapman", position: "3B", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/656305/headshot/67/current", team: "SF", value: 94.2 }
];

const MOCK_SAVANT_BARREL_LEADERS: SavantLeader[] = [
  { rank: 1, player_id: 1, player_name: "Aaron Judge", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/592450/headshot/67/current", team: "NYY", value: 26.2 },
  { rank: 2, player_id: 2, player_name: "Shohei Ohtani", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/660271/headshot/67/current", team: "LAD", value: 22.8 },
  { rank: 3, player_id: 14, player_name: "Juan Soto", position: "OF", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/665742/headshot/67/current", team: "NYY", value: 18.5 },
  { rank: 4, player_id: 12, player_name: "Giancarlo Stanton", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/519317/headshot/67/current", team: "NYY", value: 18.4 },
  { rank: 5, player_id: 15, player_name: "Brent Rooker", position: "DH", headshot_url: "https://img.mlbstatic.com/mlb-photos/image/upload/d_people:generic:headshot:67:current.png/w_213,q_auto:best/v1/people/667670/headshot/67/current", team: "OAK", value: 17.6 }
];

export const revalidate = 5; // Revalidate every 5 seconds

export default async function DashboardPage() {
  const summary = await getSummary();
  const dbGames = await getGames({ limit: 5 } as any);
  
  // Try to fetch actual leaders, fallback to mock data if empty
  const actualBatting = await getBattingLeaders("home_runs", 5);
  const actualPitching = await getPitchingLeaders("strikeouts", 5);
  const actualEvLeaders = await getSavantLeaders("avg_exit_velocity", "batter", 5);
  const actualBarrelLeaders = await getSavantLeaders("barrel_rate", "batter", 5);
  
  const battingLeaders = actualBatting.length > 0 ? actualBatting : MOCK_BATTING_LEADERS;
  const pitchingLeaders = actualPitching.length > 0 ? actualPitching : MOCK_PITCHING_LEADERS;
  const evLeaders = actualEvLeaders.length > 0 ? actualEvLeaders : MOCK_SAVANT_EV_LEADERS;
  const barrelLeaders = actualBarrelLeaders.length > 0 ? actualBarrelLeaders : MOCK_SAVANT_BARREL_LEADERS;
  
  // Format game items or provide mock game items if none returned
  const games: GameListItem[] = dbGames.length > 0 ? dbGames.slice(0, 4) : [
    { id: 1, mlb_game_pk: 1, game_date: "2024-10-30", status: "Final", home_team_name: "Los Angeles Dodgers", home_team_abbr: "LAD", away_team_name: "New York Yankees", away_team_abbr: "NYY", home_score: 7, away_score: 6, venue: "Dodger Stadium", home_logo: "https://www.mlbstatic.com/team-logos/119.svg", away_logo: "https://www.mlbstatic.com/team-logos/147.svg" },
    { id: 2, mlb_game_pk: 2, game_date: "2024-10-29", status: "Final", home_team_name: "New York Yankees", home_team_abbr: "NYY", home_score: 11, away_score: 4, away_team_name: "Los Angeles Dodgers", away_team_abbr: "LAD", venue: "Yankee Stadium", home_logo: "https://www.mlbstatic.com/team-logos/147.svg", away_logo: "https://www.mlbstatic.com/team-logos/119.svg" },
    { id: 3, mlb_game_pk: 3, game_date: "2024-10-28", status: "Final", home_team_name: "New York Yankees", home_team_abbr: "NYY", home_score: 2, away_score: 4, away_team_name: "Los Angeles Dodgers", away_team_abbr: "LAD", venue: "Yankee Stadium", home_logo: "https://www.mlbstatic.com/team-logos/147.svg", away_logo: "https://www.mlbstatic.com/team-logos/119.svg" },
  ];

  const statsCards = [
    { title: "參賽球隊", value: summary.teams || 30, description: "MLB 聯盟球隊總數", icon: Activity, color: "var(--color-primary)" },
    { title: "現役球員", value: summary.players || 159, description: "已註冊之大聯盟球員", icon: Users, color: "var(--color-secondary)" },
    { title: "賽程場次", value: summary.games || 2566, description: "2024 賽季總場次", icon: Calendar, color: "var(--color-gold)" },
    { title: "已賽場次", value: summary.completed_games || 2521, description: "已結束並記錄結果", icon: Trophy, color: "var(--color-accent)" },
  ];

  return (
    <div className="dashboard-container animate-fade-in">
      {/* Upper header with user message */}
      <header className="dashboard-header">
        <div>
          <h1>2024 賽季數據分析中心</h1>
          <p>整合即時比分、戰績排名、球員數據分析與機器學習勝率預測</p>
        </div>
        
        {/* Sync Status Badge */}
        <div className="sync-badge glass">
          <Database size={16} className="text-gradient" />
          <div>
            <span className="sync-title">資料庫狀態</span>
            <span className="sync-desc">
              {summary.batting_records > 0 ? "同步完成 (2024)" : "數據抓取與更新中..."}
            </span>
          </div>
        </div>
      </header>

      {/* Grid of stats summary */}
      <section className="stats-grid">
        {statsCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div key={i} className="stat-card glass">
              <div className="stat-icon-wrapper" style={{ backgroundColor: `rgba(${card.color === 'var(--color-primary)' ? '0,122,255' : card.color === 'var(--color-secondary)' ? '0,199,129' : card.color === 'var(--color-gold)' ? '255,204,0' : '255,59,48'}, 0.12)` }}>
                <Icon size={24} style={{ color: card.color }} />
              </div>
              <div className="stat-info">
                <h3>{card.title}</h3>
                <p className="stat-value">{card.value.toLocaleString()}</p>
                <p className="stat-desc">{card.description}</p>
              </div>
            </div>
          );
        })}
      </section>

      {/* Two column grid for Leaders and Recent Games */}
      <div className="dashboard-layout-grid">
        
        {/* Leaderboards card */}
        <section className="dashboard-section glass">
          <div className="section-header">
            <div className="section-title">
              <Trophy size={20} color="var(--color-secondary)" />
              <h2>2024 賽季數據排行榜 (全壘打 / 三振)</h2>
            </div>
            <span className="season-indicator">2024 Regular Season</span>
          </div>
          
          <div className="leaders-row">
            {/* Batting Leaders */}
            <div className="leaders-column">
              <h3>全壘打排行榜 (HR Leaders)</h3>
              <div className="leaders-list">
                {battingLeaders.map((p) => (
                  <Link key={p.player_id} href={`/players/${p.player_id}`} className="leader-item hover-effect">
                    <span className="leader-rank">{p.rank}</span>
                    <img src={p.headshot_url} alt={p.player_name} className="player-avatar" />
                    <div className="leader-player-info">
                      <span className="player-name">{p.player_name}</span>
                      <span className="player-team">{p.team} · {p.position}</span>
                    </div>
                    <div className="leader-value-info">
                      <span className="leader-value">{p.value} HR</span>
                      <span className="leader-subtext">AVG {p.avg.toFixed(3)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Pitching Leaders */}
            <div className="leaders-column">
              <h3>奪三振排行榜 (SO Leaders)</h3>
              <div className="leaders-list">
                {pitchingLeaders.map((p) => (
                  <Link key={p.player_id} href={`/players/${p.player_id}`} className="leader-item hover-effect">
                    <span className="leader-rank">{p.rank}</span>
                    <img src={p.headshot_url} alt={p.player_name} className="player-avatar" />
                    <div className="leader-player-info">
                      <span className="player-name">{p.player_name}</span>
                      <span className="player-team">{p.team} · Pitcher</span>
                    </div>
                    <div className="leader-value-info">
                      <span className="leader-value">{p.value} SO</span>
                      <span className="leader-subtext">ERA {p.era.toFixed(2)}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Recent Games Card */}
        <section className="dashboard-section glass">
          <div className="section-header">
            <div className="section-title">
              <Calendar size={20} color="var(--color-primary)" />
              <h2>近期熱門賽事與比分</h2>
            </div>
            <Link href="/games" className="view-all-link">
              查看全部 <ArrowRight size={14} />
            </Link>
          </div>

          <div className="recent-games-list">
            {games.map((game) => (
              <div key={game.id} className="recent-game-card">
                <div className="game-date-venue">
                  <span>{game.game_date}</span>
                  <span>{game.venue}</span>
                </div>
                
                <div className="game-score-row">
                  {/* Away Team */}
                  <div className="team-row">
                    {game.away_logo && <img src={game.away_logo} alt={game.away_team_name} className="team-badge" />}
                    <span className="team-name">{game.away_team_name}</span>
                    <span className="team-score">{game.away_score !== null ? game.away_score : "-"}</span>
                  </div>

                  {/* Home Team */}
                  <div className="team-row">
                    {game.home_logo && <img src={game.home_logo} alt={game.home_team_name} className="team-badge" />}
                    <span className="team-name">{game.home_team_name}</span>
                    <span className="team-score">{game.home_score !== null ? game.home_score : "-"}</span>
                  </div>
                </div>

                <div className="game-card-footer">
                  <span className={`game-status ${game.status === 'Final' ? 'final' : 'scheduled'}`}>
                    {game.status === 'Final' ? '已結束' : game.status}
                  </span>
                  <Link href={`/games?game_id=${game.id}`} className="predict-badge">
                    查看勝率預測
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </section>

      </div>

      {/* Savant Statcast Leaderboards Section */}
      <section className="dashboard-section glass" style={{ marginTop: "1rem" }}>
        <div className="section-header">
          <div className="section-title">
            <TrendingUp size={20} color="var(--color-accent)" />
            <h2>2024 Statcast 進階數據排行榜 (平均擊球速 / 出色擊球率)</h2>
          </div>
          <span className="season-indicator" style={{ backgroundColor: "rgba(255, 59, 48, 0.12)", color: "var(--color-accent)" }}>
            Statcast Leaders
          </span>
        </div>

        <div className="leaders-row">
          {/* Average Exit Velocity Leaders */}
          <div className="leaders-column">
            <h3>擊球速度排行榜 (Avg EV Leaders)</h3>
            <div className="leaders-list">
              {evLeaders.map((p) => (
                <Link key={p.player_id} href={`/players/${p.player_id}`} className="leader-item hover-effect">
                  <span className="leader-rank">{p.rank}</span>
                  <img src={p.headshot_url} alt={p.player_name} className="player-avatar" />
                  <div className="leader-player-info">
                    <span className="player-name">{p.player_name}</span>
                    <span className="player-team">{p.team} · {p.position}</span>
                  </div>
                  <div className="leader-value-info">
                    <span className="leader-value text-savant-red">{p.value.toFixed(1)} mph</span>
                    <span className="leader-subtext">擊球強度</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Barrel Rate Leaders */}
          <div className="leaders-column">
            <h3>出色擊球率排行榜 (Barrel% Leaders)</h3>
            <div className="leaders-list">
              {barrelLeaders.map((p) => (
                <Link key={p.player_id} href={`/players/${p.player_id}`} className="leader-item hover-effect">
                  <span className="leader-rank">{p.rank}</span>
                  <img src={p.headshot_url} alt={p.player_name} className="player-avatar" />
                  <div className="leader-player-info">
                    <span className="player-name">{p.player_name}</span>
                    <span className="player-team">{p.team} · {p.position}</span>
                  </div>
                  <div className="leader-value-info">
                    <span className="leader-value text-savant-red">{p.value.toFixed(1)}%</span>
                    <span className="leader-subtext">出色擊球占比</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
