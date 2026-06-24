import Link from "next/link";
import { getTeam, getTeamRoster, PlayerListItem } from "@/lib/api";
import { MapPin, Trophy, Users, ChevronLeft } from "lucide-react";
import { notFound } from "next/navigation";

export const revalidate = 5; // Revalidate every 5 seconds

// Helper to group roster players by general position
function groupRoster(players: PlayerListItem[]) {
  const grouped: { [key: string]: PlayerListItem[] } = {
    "投手 (Pitchers)": [],
    "捕手 (Catchers)": [],
    "內野手 (Infielders)": [],
    "外野手 (Outfielders)": [],
    "其他 (Others)": [],
  };

  players.forEach((player) => {
    const pos = player.primary_position;
    if (["P", "SP", "RP", "LHP", "RHP"].includes(pos)) {
      grouped["投手 (Pitchers)"].push(player);
    } else if (pos === "C") {
      grouped["捕手 (Catchers)"].push(player);
    } else if (["1B", "2B", "3B", "SS", "INF", "IF"].includes(pos)) {
      grouped["內野手 (Infielders)"].push(player);
    } else if (["LF", "CF", "RF", "OF"].includes(pos)) {
      grouped["外野手 (Outfielders)"].push(player);
    } else {
      grouped["其他 (Others)"].push(player);
    }
  });

  // Remove empty groups
  return Object.fromEntries(
    Object.entries(grouped).filter(([_, list]) => list.length > 0)
  );
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function TeamDetailPage({ params }: PageProps) {
  const resolvedParams = await params;
  const teamId = Number(resolvedParams.id);
  
  if (isNaN(teamId)) {
    notFound();
  }

  const team = await getTeam(teamId);
  if (!team) {
    notFound();
  }

  const roster = await getTeamRoster(teamId);
  const groupedRoster = groupRoster(roster);

  const leagueName = team.league === "AL" ? "美國聯盟 (American League)" : "國家聯盟 (National League)";
  const divisionName = `${team.division}區 (East/Central/West)`;

  return (
    <div className="team-detail-container animate-fade-in">
      {/* Back Button */}
      <div className="back-nav">
        <Link href="/teams" className="back-link">
          <ChevronLeft size={16} /> <span>返回所有球隊</span>
        </Link>
      </div>

      {/* Team Profile Header Hero */}
      <section className="team-hero glass">
        {team.logo_url && (
          <img src={team.logo_url} alt={team.name} className="team-logo-lg" />
        )}
        
        <div className="team-title-info">
          <div className="league-breadcrumbs">
            <span>{leagueName}</span>
            <span className="dot">•</span>
            <span>{team.division}組</span>
          </div>
          <h1>{team.name}</h1>
          
          <div className="team-meta-row">
            <div className="meta-item">
              <MapPin size={16} color="var(--text-muted)" />
              <span>{team.venue_name || "未知球場"}</span>
            </div>
            <div className="meta-item">
              <Users size={16} color="var(--text-muted)" />
              <span>現役陣容：{roster.length} 人</span>
            </div>
          </div>
        </div>

        {/* Team Standing Summary Box */}
        <div className="team-standing-box glass">
          <div className="standing-icon-header">
            <Trophy size={18} color="var(--color-gold)" />
            <span>2024 戰績</span>
          </div>
          <div className="standing-stats">
            <div className="stat-num-col">
              <span className="num">{team.wins || 0}</span>
              <span className="label">勝</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-num-col">
              <span className="num">{team.losses || 0}</span>
              <span className="label">敗</span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-num-col">
              <span className="num">
                {team.win_pct !== undefined ? team.win_pct.toFixed(3) : ".000"}
              </span>
              <span className="label">勝率</span>
            </div>
          </div>
          {team.division_rank && (
            <div className="standing-rank-badge">
              分區排名第 {team.division_rank} 名 {team.streak && `(${team.streak})`}
            </div>
          )}
        </div>
      </section>

      {/* Roster Section */}
      <section className="roster-section">
        <div className="roster-header">
          <h2>球隊現役球員名冊</h2>
          <p>Active Roster (按守備位置分組)</p>
        </div>

        {roster.length === 0 ? (
          <div className="empty-roster glass flex-center">
            <p>尚未抓取此球隊的球員名單。請稍候，背景同步正在下載中...</p>
          </div>
        ) : (
          <div className="roster-groups-stack">
            {Object.entries(groupedRoster).map(([groupName, players]) => (
              <div key={groupName} className="roster-group-card glass">
                <div className="group-title">
                  <h3>{groupName}</h3>
                  <span className="count-badge">{players.length} 人</span>
                </div>

                <div className="players-grid">
                  {players.map((player) => (
                    <Link 
                      key={player.id} 
                      href={`/players/${player.id}`} 
                      className="player-roster-card"
                    >
                      <div className="player-avatar-wrapper">
                        <img 
                          src={player.headshot_url} 
                          alt={player.full_name} 
                          className="player-headshot" 
                        />
                        {player.jersey_number && (
                          <span className="player-number">#{player.jersey_number}</span>
                        )}
                      </div>
                      <div className="player-meta">
                        <span className="player-name">{player.full_name}</span>
                        <span className="player-position">{player.primary_position}</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
