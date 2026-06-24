import Link from "next/link";
import { getPlayers } from "@/lib/api";
import { Users, Search, ChevronLeft, ChevronRight, User } from "lucide-react";

export const revalidate = 0; // Dynamic page, do not cache statically

interface PageProps {
  searchParams: Promise<{
    search?: string;
    position?: string;
    page?: string;
  }>;
}

const POSITIONS = [
  { abbr: "P", name: "投手 (Pitcher)" },
  { abbr: "C", name: "捕手 (Catcher)" },
  { abbr: "1B", name: "一壘手 (First Base)" },
  { abbr: "2B", name: "二壘手 (Second Base)" },
  { abbr: "3B", name: "三壘手 (Third Base)" },
  { abbr: "SS", name: "游擊手 (Shortstop)" },
  { abbr: "LF", name: "左外野手 (Left Field)" },
  { abbr: "CF", name: "中外野手 (Center Field)" },
  { abbr: "RF", name: "右外野手 (Right Field)" },
  { abbr: "DH", name: "指定打擊 (Designated Hitter)" },
];

export default async function PlayersPage({ searchParams }: PageProps) {
  const resolvedSearchParams = await searchParams;
  const search = resolvedSearchParams.search || "";
  const position = resolvedSearchParams.position || "";
  const page = Number(resolvedSearchParams.page) || 1;
  const perPage = 24;

  const result = await getPlayers({
    search,
    position,
    page,
    perPage,
  });

  const totalPages = Math.ceil(result.total / perPage);

  // Helper to create page URLs
  const getPageUrl = (targetPage: number) => {
    const queryParts = [];
    if (search) queryParts.push(`search=${encodeURIComponent(search)}`);
    if (position) queryParts.push(`position=${encodeURIComponent(position)}`);
    queryParts.push(`page=${targetPage}`);
    return `?${queryParts.join("&")}`;
  };

  return (
    <div className="players-container animate-fade-in">
      <header className="players-header">
        <div>
          <h1>MLB 球員名冊與數據</h1>
          <p>搜尋所有大聯盟球員，查看其詳細個人資訊與賽季逐場數據</p>
        </div>
        
        <div className="players-badge glass">
          <Users size={20} color="var(--color-secondary)" />
          <span>共 {result.total} 位符合條件</span>
        </div>
      </header>

      {/* Search and Filter Form */}
      <section className="search-filter-section glass">
        <form method="GET" action="/players" className="search-form">
          <div className="input-group">
            <Search size={18} className="input-icon" />
            <input 
              type="text" 
              name="search" 
              placeholder="搜尋球員姓名 (例如: Aaron Judge)..." 
              defaultValue={search}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <select name="position" defaultValue={position} className="position-select">
              <option value="">所有守備位置</option>
              {POSITIONS.map((pos) => (
                <option key={pos.abbr} value={pos.abbr}>
                  {pos.abbr} - {pos.name}
                </option>
              ))}
            </select>
          </div>

          <button type="submit" className="submit-btn">
            篩選搜尋
          </button>
          
          {(search || position) && (
            <Link href="/players" className="clear-btn flex-center">
              重設
            </Link>
          )}
        </form>
      </section>

      {/* Roster Cards Grid */}
      {result.data.length === 0 ? (
        <div className="empty-results glass flex-center">
          <User size={48} color="var(--text-muted)" />
          <p>找不到符合條件的球員，請嘗試更換關鍵字或重設篩選條件。</p>
        </div>
      ) : (
        <>
          <section className="players-grid">
            {result.data.map((player) => (
              <Link key={player.id} href={`/players/${player.id}`} className="player-card glass">
                <div className="player-avatar-bg">
                  <img 
                    src={player.headshot_url} 
                    alt={player.full_name} 
                    className="player-headshot-lg" 
                  />
                  {player.jersey_number && (
                    <span className="jersey-number">#{player.jersey_number}</span>
                  )}
                </div>

                <div className="player-info-body">
                  <h3>{player.full_name}</h3>
                  <div className="player-badges">
                    <span className="badge-team">
                      {player.team_abbreviation || "無球隊"}
                    </span>
                    <span className="badge-position">
                      {player.primary_position}
                    </span>
                  </div>
                  <p className="team-fullname">
                    {player.team_name || "自由球員 / 未知"}
                  </p>
                </div>

                <div className="player-card-footer">
                  <span>查看個人數據</span>
                  <span className="arrow">→</span>
                </div>
              </Link>
            ))}
          </section>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <nav className="pagination">
              {page > 1 ? (
                <Link href={getPageUrl(page - 1)} className="page-link glass">
                  <ChevronLeft size={16} /> <span>上一頁</span>
                </Link>
              ) : (
                <span className="page-link disabled glass">
                  <ChevronLeft size={16} /> <span>上一頁</span>
                </span>
              )}

              <span className="page-indicator">
                第 {page} 頁 / 共 {totalPages} 頁
              </span>

              {page < totalPages ? (
                <Link href={getPageUrl(page + 1)} className="page-link glass">
                  <span>下一頁</span> <ChevronRight size={16} />
                </Link>
              ) : (
                <span className="page-link disabled glass">
                  <span>下一頁</span> <ChevronRight size={16} />
                </span>
              )}
            </nav>
          )}
        </>
      )}
    </div>
  );
}
