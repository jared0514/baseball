import Link from "next/link";
import { getGames, GameListItem } from "@/lib/api";
import { Calendar, Brain, Trophy, ShieldAlert, CheckCircle2, XCircle } from "lucide-react";
import GenAIGameAnalysis from "@/components/GenAIGameAnalysis";

export const revalidate = 0; // Dynamic schedule, do not cache

interface PageProps {
  searchParams: Promise<{
    date?: string;
  }>;
}

// Fallback Mock Games for 2024-09-28 (a exciting final weekend of regular season)
const MOCK_GAMES: GameListItem[] = [
  { id: 101, mlb_game_pk: 1, game_date: "2024-09-28", status: "Final", home_team_name: "New York Yankees", home_team_abbr: "NYY", away_team_name: "Pittsburgh Pirates", away_team_abbr: "PIT", home_score: 4, away_score: 9, venue: "Yankee Stadium", home_logo: "https://www.mlbstatic.com/team-logos/147.svg", away_logo: "https://www.mlbstatic.com/team-logos/134.svg", home_win_prob: 68, away_win_prob: 32 },
  { id: 102, mlb_game_pk: 2, game_date: "2024-09-28", status: "Final", home_team_name: "Los Angeles Dodgers", home_team_abbr: "LAD", away_team_name: "San Diego Padres", away_team_abbr: "SD", home_score: 5, away_score: 0, venue: "Dodger Stadium", home_logo: "https://www.mlbstatic.com/team-logos/119.svg", away_logo: "https://www.mlbstatic.com/team-logos/135.svg", home_win_prob: 57, away_win_prob: 43 },
  { id: 103, mlb_game_pk: 3, game_date: "2024-09-28", status: "Final", home_team_name: "Boston Red Sox", home_team_abbr: "BOS", away_team_name: "Tampa Bay Rays", away_team_abbr: "TB", home_score: 2, away_score: 7, venue: "Fenway Park", home_logo: "https://www.mlbstatic.com/team-logos/111.svg", away_logo: "https://www.mlbstatic.com/team-logos/139.svg", home_win_prob: 49, away_win_prob: 51 },
  { id: 104, mlb_game_pk: 4, game_date: "2024-09-28", status: "Final", home_team_name: "San Francisco Giants", home_team_abbr: "SF", away_team_name: "St. Louis Cardinals", away_team_abbr: "STL", home_score: 3, away_score: 6, venue: "Oracle Park", home_logo: "https://www.mlbstatic.com/team-logos/137.svg", away_logo: "https://www.mlbstatic.com/team-logos/138.svg", home_win_prob: 48, away_win_prob: 52 },
];

export default async function GamesPage({ searchParams }: PageProps) {
  const resolvedSearchParams = await searchParams;
  // Default to a date in the 2024 season that is highly populated (e.g. final Saturday)
  const dateStr = resolvedSearchParams.date || "2024-09-28";

  const dbGames = await getGames({ date: dateStr });

  const games = dbGames.length > 0 ? dbGames : MOCK_GAMES.map(g => ({ ...g, game_date: dateStr }));

  return (
    <div className="games-container animate-fade-in">
      <header className="games-header">
        <div>
          <h1>MLB 賽事日程與預測</h1>
          <p>瀏覽 2024 賽季每日比賽結果，並查看 AI 基於球隊表現訓練的勝率預測</p>
        </div>
        
        <div className="games-badge glass">
          <Calendar size={20} color="var(--color-primary)" />
          <span>賽事日期：{dateStr}</span>
        </div>
      </header>

      {/* Date Selection Panel */}
      <section className="date-selector-section glass">
        <form method="GET" action="/games" className="date-form">
          <label htmlFor="date-picker">選擇日期：</label>
          <input 
            type="date" 
            id="date-picker" 
            name="date" 
            defaultValue={dateStr}
            min="2024-03-20"
            max="2024-10-30"
            className="date-input"
          />
          <button type="submit" className="date-submit-btn">
            跳轉日期
          </button>
          
          <span className="helper-text">
            * 提示：2024 正規賽季範圍約在 2024-03-20 至 2024-10-30 之間。
          </span>
        </form>
      </section>

      {/* Games List Grid */}
      <div className="games-grid">
        {games.map((game) => {
          const prediction = {
            homeProb: game.home_win_prob ?? 50,
            awayProb: game.away_win_prob ?? 50,
          };
          
          // Check if prediction was correct
          let isCorrect = null;
          if (game.status === "Final" && game.home_score !== null && game.away_score !== null) {
            const homeWon = game.home_score > game.away_score;
            const predictedHomeWon = prediction.homeProb > prediction.awayProb;
            isCorrect = homeWon === predictedHomeWon;
          }

          return (
            <div key={game.id} className="game-card-large glass">
              
              {/* Card Top Header */}
              <div className="card-header">
                <span className="venue-name">{game.venue}</span>
                <span className={`status-badge ${game.status === 'Final' ? 'final' : 'scheduled'}`}>
                  {game.status === 'Final' ? '已結束' : game.status}
                </span>
              </div>

              {/* Matching Score Board Grid */}
              <div className="scoreboard-row">
                {/* Away Team Column */}
                <div className="team-col text-right">
                  {game.away_logo && <img src={game.away_logo} alt={game.away_team_name} className="team-logo" />}
                  <h3>{game.away_team_name}</h3>
                  <span className="team-abbr">{game.away_team_abbr}</span>
                </div>

                {/* Score Center Column */}
                <div className="score-center">
                  {game.status === "Final" ? (
                    <div className="scores-display">
                      <span className={`score ${game.away_score! > game.home_score! ? 'winner' : 'loser'}`}>
                        {game.away_score}
                      </span>
                      <span className="score-divider">:</span>
                      <span className={`score ${game.home_score! > game.away_score! ? 'winner' : 'loser'}`}>
                        {game.home_score}
                      </span>
                    </div>
                  ) : (
                    <div className="scheduled-time">VS</div>
                  )}
                </div>

                {/* Home Team Column */}
                <div className="team-col text-left">
                  {game.home_logo && <img src={game.home_logo} alt={game.home_team_name} className="team-logo" />}
                  <h3>{game.home_team_name}</h3>
                  <span className="team-abbr">{game.home_team_abbr}</span>
                </div>
              </div>

              {/* Machine Learning Prediction Drawer */}
              <div className="prediction-box">
                <div className="prediction-box-header">
                  <div className="ai-title">
                    <Brain size={18} className="text-gradient" />
                    <h4>AI 勝率預測模型</h4>
                  </div>
                  
                  {isCorrect !== null && (
                    <div className={`prediction-result ${isCorrect ? 'correct' : 'incorrect'}`}>
                      {isCorrect ? (
                        <>
                          <CheckCircle2 size={14} /> <span>AI 預測成功</span>
                        </>
                      ) : (
                        <>
                          <XCircle size={14} /> <span>預測失誤</span>
                        </>
                      )}
                    </div>
                  )}
                </div>

                {/* Win Prob bar chart */}
                <div className="prob-bar-container">
                  <div className="prob-labels">
                    <span>{game.away_team_abbr} {prediction.awayProb}%</span>
                    <span>{game.home_team_abbr} {prediction.homeProb}%</span>
                  </div>
                  
                  <div className="prob-bar-track">
                    <div 
                      className="prob-bar-fill away" 
                      style={{ width: `${prediction.awayProb}%` }}
                    ></div>
                    <div 
                      className="prob-bar-fill home" 
                      style={{ width: `${prediction.homeProb}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              {/* GenAI Pre-game Analysis */}
              <GenAIGameAnalysis gameId={game.id} defaultExpanded={false} />

            </div>
          );
        })}
      </div>
    </div>
  );
}
