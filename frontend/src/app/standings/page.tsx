import { getStandings, DivisionStandings, StandingsEntry } from "@/lib/api";
import { Trophy, Award } from "lucide-react";

// Robust Fallback Mock Data for 2024 Final MLB Standings — All 6 Divisions
const MOCK_STANDINGS: DivisionStandings[] = [
  {
    league: "AL",
    division: "East",
    teams: [
      { team: { id: 1, mlb_id: 147, name: "New York Yankees", abbreviation: "NYY", league: "AL", division: "East", venue_name: "Yankee Stadium", logo_url: "https://www.mlbstatic.com/team-logos/147.svg" }, wins: 94, losses: 68, win_pct: 0.580, games_back: 0.0, runs_scored: 815, runs_allowed: 668, run_diff: 147, division_rank: 1, streak: "W1" },
      { team: { id: 2, mlb_id: 110, name: "Baltimore Orioles", abbreviation: "BAL", league: "AL", division: "East", venue_name: "Oriole Park", logo_url: "https://www.mlbstatic.com/team-logos/110.svg" }, wins: 91, losses: 71, win_pct: 0.562, games_back: 3.0, runs_scored: 786, runs_allowed: 697, run_diff: 89, division_rank: 2, streak: "W3" },
      { team: { id: 3, mlb_id: 111, name: "Boston Red Sox", abbreviation: "BOS", league: "AL", division: "East", venue_name: "Fenway Park", logo_url: "https://www.mlbstatic.com/team-logos/111.svg" }, wins: 81, losses: 81, win_pct: 0.500, games_back: 13.0, runs_scored: 796, runs_allowed: 789, run_diff: 7, division_rank: 3, streak: "L1" },
      { team: { id: 4, mlb_id: 139, name: "Tampa Bay Rays", abbreviation: "TB", league: "AL", division: "East", venue_name: "Tropicana Field", logo_url: "https://www.mlbstatic.com/team-logos/139.svg" }, wins: 80, losses: 82, win_pct: 0.494, games_back: 14.0, runs_scored: 604, runs_allowed: 690, run_diff: -86, division_rank: 4, streak: "W2" },
      { team: { id: 5, mlb_id: 141, name: "Toronto Blue Jays", abbreviation: "TOR", league: "AL", division: "East", venue_name: "Rogers Centre", logo_url: "https://www.mlbstatic.com/team-logos/141.svg" }, wins: 74, losses: 88, win_pct: 0.457, games_back: 20.0, runs_scored: 671, runs_allowed: 759, run_diff: -88, division_rank: 5, streak: "L2" },
    ]
  },
  {
    league: "AL",
    division: "Central",
    teams: [
      { team: { id: 6, mlb_id: 116, name: "Cleveland Guardians", abbreviation: "CLE", league: "AL", division: "Central", venue_name: "Progressive Field", logo_url: "https://www.mlbstatic.com/team-logos/116.svg" }, wins: 92, losses: 69, win_pct: 0.571, games_back: 0.0, runs_scored: 708, runs_allowed: 621, run_diff: 87, division_rank: 1, streak: "W2" },
      { team: { id: 7, mlb_id: 118, name: "Kansas City Royals", abbreviation: "KC", league: "AL", division: "Central", venue_name: "Kauffman Stadium", logo_url: "https://www.mlbstatic.com/team-logos/118.svg" }, wins: 86, losses: 76, win_pct: 0.531, games_back: 6.5, runs_scored: 735, runs_allowed: 645, run_diff: 90, division_rank: 2, streak: "W1" },
      { team: { id: 8, mlb_id: 114, name: "Detroit Tigers", abbreviation: "DET", league: "AL", division: "Central", venue_name: "Comerica Park", logo_url: "https://www.mlbstatic.com/team-logos/114.svg" }, wins: 86, losses: 76, win_pct: 0.531, games_back: 6.5, runs_scored: 656, runs_allowed: 642, run_diff: 14, division_rank: 3, streak: "L1" },
      { team: { id: 9, mlb_id: 142, name: "Minnesota Twins", abbreviation: "MIN", league: "AL", division: "Central", venue_name: "Target Field", logo_url: "https://www.mlbstatic.com/team-logos/142.svg" }, wins: 82, losses: 80, win_pct: 0.506, games_back: 10.5, runs_scored: 740, runs_allowed: 718, run_diff: 22, division_rank: 4, streak: "L3" },
      { team: { id: 10, mlb_id: 145, name: "Chicago White Sox", abbreviation: "CWS", league: "AL", division: "Central", venue_name: "Guaranteed Rate Field", logo_url: "https://www.mlbstatic.com/team-logos/145.svg" }, wins: 41, losses: 121, win_pct: 0.253, games_back: 51.5, runs_scored: 507, runs_allowed: 831, run_diff: -324, division_rank: 5, streak: "W1" },
    ]
  },
  {
    league: "AL",
    division: "West",
    teams: [
      { team: { id: 11, mlb_id: 117, name: "Houston Astros", abbreviation: "HOU", league: "AL", division: "West", venue_name: "Minute Maid Park", logo_url: "https://www.mlbstatic.com/team-logos/117.svg" }, wins: 88, losses: 73, win_pct: 0.547, games_back: 0.0, runs_scored: 746, runs_allowed: 648, run_diff: 98, division_rank: 1, streak: "W2" },
      { team: { id: 12, mlb_id: 136, name: "Seattle Mariners", abbreviation: "SEA", league: "AL", division: "West", venue_name: "T-Mobile Park", logo_url: "https://www.mlbstatic.com/team-logos/136.svg" }, wins: 85, losses: 77, win_pct: 0.525, games_back: 3.0, runs_scored: 625, runs_allowed: 618, run_diff: 7, division_rank: 2, streak: "L1" },
      { team: { id: 13, mlb_id: 140, name: "Texas Rangers", abbreviation: "TEX", league: "AL", division: "West", venue_name: "Globe Life Field", logo_url: "https://www.mlbstatic.com/team-logos/140.svg" }, wins: 78, losses: 84, win_pct: 0.481, games_back: 10.0, runs_scored: 718, runs_allowed: 707, run_diff: 11, division_rank: 3, streak: "W1" },
      { team: { id: 14, mlb_id: 108, name: "Los Angeles Angels", abbreviation: "LAA", league: "AL", division: "West", venue_name: "Angel Stadium", logo_url: "https://www.mlbstatic.com/team-logos/108.svg" }, wins: 63, losses: 99, win_pct: 0.389, games_back: 25.0, runs_scored: 628, runs_allowed: 807, run_diff: -179, division_rank: 4, streak: "L4" },
      { team: { id: 15, mlb_id: 133, name: "Oakland Athletics", abbreviation: "OAK", league: "AL", division: "West", venue_name: "Oakland Coliseum", logo_url: "https://www.mlbstatic.com/team-logos/133.svg" }, wins: 69, losses: 93, win_pct: 0.426, games_back: 19.0, runs_scored: 635, runs_allowed: 780, run_diff: -145, division_rank: 5, streak: "L2" },
    ]
  },
  {
    league: "NL",
    division: "East",
    teams: [
      { team: { id: 16, mlb_id: 143, name: "Philadelphia Phillies", abbreviation: "PHI", league: "NL", division: "East", venue_name: "Citizens Bank Park", logo_url: "https://www.mlbstatic.com/team-logos/143.svg" }, wins: 95, losses: 67, win_pct: 0.586, games_back: 0.0, runs_scored: 799, runs_allowed: 655, run_diff: 144, division_rank: 1, streak: "W3" },
      { team: { id: 17, mlb_id: 144, name: "Atlanta Braves", abbreviation: "ATL", league: "NL", division: "East", venue_name: "Truist Park", logo_url: "https://www.mlbstatic.com/team-logos/144.svg" }, wins: 89, losses: 73, win_pct: 0.549, games_back: 6.0, runs_scored: 770, runs_allowed: 684, run_diff: 86, division_rank: 2, streak: "W1" },
      { team: { id: 18, mlb_id: 121, name: "New York Mets", abbreviation: "NYM", league: "NL", division: "East", venue_name: "Citi Field", logo_url: "https://www.mlbstatic.com/team-logos/121.svg" }, wins: 89, losses: 73, win_pct: 0.549, games_back: 6.0, runs_scored: 758, runs_allowed: 684, run_diff: 74, division_rank: 3, streak: "W5" },
      { team: { id: 19, mlb_id: 120, name: "Washington Nationals", abbreviation: "WSH", league: "NL", division: "East", venue_name: "Nationals Park", logo_url: "https://www.mlbstatic.com/team-logos/120.svg" }, wins: 71, losses: 91, win_pct: 0.438, games_back: 24.0, runs_scored: 669, runs_allowed: 754, run_diff: -85, division_rank: 4, streak: "L1" },
      { team: { id: 20, mlb_id: 146, name: "Miami Marlins", abbreviation: "MIA", league: "NL", division: "East", venue_name: "loanDepot park", logo_url: "https://www.mlbstatic.com/team-logos/146.svg" }, wins: 62, losses: 100, win_pct: 0.383, games_back: 33.0, runs_scored: 553, runs_allowed: 749, run_diff: -196, division_rank: 5, streak: "L3" },
    ]
  },
  {
    league: "NL",
    division: "Central",
    teams: [
      { team: { id: 21, mlb_id: 158, name: "Milwaukee Brewers", abbreviation: "MIL", league: "NL", division: "Central", venue_name: "American Family Field", logo_url: "https://www.mlbstatic.com/team-logos/158.svg" }, wins: 93, losses: 69, win_pct: 0.574, games_back: 0.0, runs_scored: 766, runs_allowed: 656, run_diff: 110, division_rank: 1, streak: "W2" },
      { team: { id: 22, mlb_id: 112, name: "Chicago Cubs", abbreviation: "CHC", league: "NL", division: "Central", venue_name: "Wrigley Field", logo_url: "https://www.mlbstatic.com/team-logos/112.svg" }, wins: 83, losses: 79, win_pct: 0.512, games_back: 10.0, runs_scored: 700, runs_allowed: 653, run_diff: 47, division_rank: 2, streak: "L2" },
      { team: { id: 23, mlb_id: 113, name: "Cincinnati Reds", abbreviation: "CIN", league: "NL", division: "Central", venue_name: "Great American Ball Park", logo_url: "https://www.mlbstatic.com/team-logos/113.svg" }, wins: 77, losses: 85, win_pct: 0.475, games_back: 16.0, runs_scored: 723, runs_allowed: 756, run_diff: -33, division_rank: 3, streak: "W1" },
      { team: { id: 24, mlb_id: 138, name: "St. Louis Cardinals", abbreviation: "STL", league: "NL", division: "Central", venue_name: "Busch Stadium", logo_url: "https://www.mlbstatic.com/team-logos/138.svg" }, wins: 71, losses: 91, win_pct: 0.438, games_back: 22.0, runs_scored: 621, runs_allowed: 748, run_diff: -127, division_rank: 4, streak: "L1" },
      { team: { id: 25, mlb_id: 134, name: "Pittsburgh Pirates", abbreviation: "PIT", league: "NL", division: "Central", venue_name: "PNC Park", logo_url: "https://www.mlbstatic.com/team-logos/134.svg" }, wins: 76, losses: 86, win_pct: 0.469, games_back: 17.0, runs_scored: 651, runs_allowed: 752, run_diff: -101, division_rank: 5, streak: "L1" },
    ]
  },
  {
    league: "NL",
    division: "West",
    teams: [
      { team: { id: 26, mlb_id: 119, name: "Los Angeles Dodgers", abbreviation: "LAD", league: "NL", division: "West", venue_name: "Dodger Stadium", logo_url: "https://www.mlbstatic.com/team-logos/119.svg" }, wins: 98, losses: 64, win_pct: 0.605, games_back: 0.0, runs_scored: 842, runs_allowed: 686, run_diff: 156, division_rank: 1, streak: "W5" },
      { team: { id: 27, mlb_id: 135, name: "San Diego Padres", abbreviation: "SD", league: "NL", division: "West", venue_name: "Petco Park", logo_url: "https://www.mlbstatic.com/team-logos/135.svg" }, wins: 93, losses: 69, win_pct: 0.574, games_back: 5.0, runs_scored: 760, runs_allowed: 669, run_diff: 91, division_rank: 2, streak: "L1" },
      { team: { id: 28, mlb_id: 109, name: "Arizona Diamondbacks", abbreviation: "AZ", league: "NL", division: "West", venue_name: "Chase Field", logo_url: "https://www.mlbstatic.com/team-logos/109.svg" }, wins: 89, losses: 73, win_pct: 0.549, games_back: 9.0, runs_scored: 886, runs_allowed: 788, run_diff: 98, division_rank: 3, streak: "W2" },
      { team: { id: 29, mlb_id: 137, name: "San Francisco Giants", abbreviation: "SF", league: "NL", division: "West", venue_name: "Oracle Park", logo_url: "https://www.mlbstatic.com/team-logos/137.svg" }, wins: 80, losses: 82, win_pct: 0.494, games_back: 18.0, runs_scored: 699, runs_allowed: 716, run_diff: -17, division_rank: 4, streak: "L2" },
      { team: { id: 30, mlb_id: 115, name: "Colorado Rockies", abbreviation: "COL", league: "NL", division: "West", venue_name: "Coors Field", logo_url: "https://www.mlbstatic.com/team-logos/115.svg" }, wins: 61, losses: 101, win_pct: 0.377, games_back: 37.0, runs_scored: 708, runs_allowed: 902, run_diff: -194, division_rank: 5, streak: "L1" },
    ]
  }
];

// Division display order and Chinese names mapping
const DIVISION_ORDER = ["East", "Central", "West"];
const DIVISION_CN: Record<string, Record<string, string>> = {
  AL: { East: "美東", Central: "美中", West: "美西" },
  NL: { East: "國東", Central: "國中", West: "國西" },
};
const LEAGUE_CN: Record<string, string> = {
  AL: "美國聯盟 (American League)",
  NL: "國家聯盟 (National League)",
};

// Sort divisions into proper order
function sortDivisions(standings: DivisionStandings[]): DivisionStandings[] {
  const sorted: DivisionStandings[] = [];
  for (const league of ["AL", "NL"]) {
    for (const div of DIVISION_ORDER) {
      const found = standings.find(s => s.league === league && s.division === div);
      if (found) sorted.push(found);
    }
  }
  return sorted;
}

export const revalidate = 10;

export default async function StandingsPage() {
  const dbStandings = await getStandings();
  const rawStandings = dbStandings.length > 0 ? dbStandings : MOCK_STANDINGS;
  const standings = sortDivisions(rawStandings);

  // Group standings by league
  const leagueOrder = ["AL", "NL"];

  return (
    <div className="standings-container animate-fade-in">
      <header className="standings-header">
        <div>
          <h1>MLB 聯盟分區戰績表</h1>
          <p>2024 賽季美聯與國聯各分區排名、勝率及得失分差</p>
        </div>
        
        <div className="trophy-badge glass">
          <Trophy size={20} color="var(--color-gold)" />
          <span>Regular Season Standings</span>
        </div>
      </header>

      {leagueOrder.map((league) => {
        const leagueStandings = standings.filter(s => s.league === league);
        const leagueFullName = LEAGUE_CN[league] || league;

        return (
          <section key={league} className="league-section">
            <h2 className="league-title">
              <Award size={22} className="league-icon" />
              {leagueFullName}
            </h2>

            <div className="divisions-grid">
              {leagueStandings.map((div) => {
                const divCnName = DIVISION_CN[league]?.[div.division] || div.division;
                
                return (
                  <div key={`${league}-${div.division}`} className="division-card glass">
                    <div className="division-header">
                      <h3>
                        <span className="division-badge-label">{divCnName}</span>
                        <span className="division-en-label">{league} {div.division}</span>
                      </h3>
                    </div>

                    <div className="table-responsive">
                      <table className="standings-table">
                        <thead>
                          <tr>
                            <th className="th-rank">名次</th>
                            <th className="th-team">球隊</th>
                            <th className="th-num">勝</th>
                            <th className="th-num">敗</th>
                            <th className="th-num">勝率</th>
                            <th className="th-num">勝差</th>
                            <th className="th-num">得分</th>
                            <th className="th-num">失分</th>
                            <th className="th-num">得失分差</th>
                            <th className="th-streak">近況</th>
                          </tr>
                        </thead>
                        <tbody>
                          {div.teams.map((entry: StandingsEntry) => (
                            <tr key={entry.team.id} className="team-row">
                              <td className="td-rank">
                                <span className={`rank-badge rank-${entry.division_rank}`}>
                                  {entry.division_rank}
                                </span>
                              </td>
                              <td className="td-team">
                                <div className="team-info">
                                  {entry.team.logo_url && (
                                    <img 
                                      src={entry.team.logo_url} 
                                      alt={entry.team.name} 
                                      className="team-logo" 
                                    />
                                  )}
                                  <span className="team-name" title={entry.team.name}>
                                    {entry.team.name}
                                  </span>
                                  <span className="team-abbr">
                                    {entry.team.abbreviation}
                                  </span>
                                </div>
                              </td>
                              <td className="td-num font-semibold">{entry.wins}</td>
                              <td className="td-num font-semibold">{entry.losses}</td>
                              <td className="td-num text-secondary">
                                {entry.win_pct.toFixed(3)}
                              </td>
                              <td className="td-num text-secondary">
                                {entry.games_back === 0 ? "—" : entry.games_back.toFixed(1)}
                              </td>
                              <td className="td-num text-muted">{entry.runs_scored}</td>
                              <td className="td-num text-muted">{entry.runs_allowed}</td>
                              <td className="td-num">
                                <span className={`diff-badge ${entry.run_diff >= 0 ? 'pos' : 'neg'}`}>
                                  {entry.run_diff >= 0 ? `+${entry.run_diff}` : entry.run_diff}
                                </span>
                              </td>
                              <td className="td-streak">
                                <span className={`streak-badge ${entry.streak.startsWith('W') ? 'win' : 'loss'}`}>
                                  {entry.streak}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        );
      })}
    </div>
  );
}
