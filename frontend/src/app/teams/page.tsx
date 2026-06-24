import Link from "next/link";
import { getTeams, Team } from "@/lib/api";
import { Shield, MapPin } from "lucide-react";

export const revalidate = 60; // Revalidate every minute

export default async function TeamsPage() {
  const teams = await getTeams();

  // Group teams by League and Division
  const groupedTeams: { [key: string]: Team[] } = {};
  
  teams.forEach((team) => {
    const key = `${team.league} ${team.division}`;
    if (!groupedTeams[key]) {
      groupedTeams[key] = [];
    }
    groupedTeams[key].push(team);
  });

  // Sort groups alphabetically (AL East, AL Central, AL West, NL East...)
  const sortedGroupKeys = Object.keys(groupedTeams).sort((a, b) => {
    // Standard sorting: AL East, AL Central, AL West, NL East...
    return a.localeCompare(b);
  });

  return (
    <div className="teams-container animate-fade-in">
      <header className="teams-header">
        <div>
          <h1>MLB 聯盟球隊目錄</h1>
          <p>瀏覽大聯盟 30 支球隊，查看陣容名冊與詳細數據分析</p>
        </div>
        
        <div className="teams-badge glass">
          <Shield size={20} color="var(--color-primary)" />
          <span>30 Active Franchises</span>
        </div>
      </header>

      {sortedGroupKeys.map((groupKey) => {
        const groupTeams = groupedTeams[groupKey];
        const [league, division] = groupKey.split(" ");
        const leagueName = league === "AL" ? "美國聯盟 (AL)" : "國家聯盟 (NL)";
        
        return (
          <section key={groupKey} className="division-section">
            <h2 className="division-title">
              <span className="league-indicator">{league}</span>
              <span>{division} 組</span>
            </h2>

            <div className="teams-grid">
              {groupTeams.map((team) => (
                <Link key={team.id} href={`/teams/${team.id}`} className="team-card glass">
                  <div className="team-card-header">
                    <span className="team-abbr">{team.abbreviation}</span>
                  </div>
                  
                  <div className="team-card-body">
                    {team.logo_url && (
                      <img src={team.logo_url} alt={team.name} className="team-logo" />
                    )}
                    <h3>{team.name}</h3>
                    <div className="venue-info">
                      <MapPin size={14} color="var(--text-muted)" />
                      <span>{team.venue_name || "未知球場"}</span>
                    </div>
                  </div>

                  <div className="team-card-footer">
                    <span>進入球隊頁面</span>
                    <span className="arrow">→</span>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
