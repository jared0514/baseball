import sqlite3
conn = sqlite3.connect('data/mlb.db')
c = conn.cursor()

# Batting AVG leaders
c.execute("""
  SELECT p.full_name, t.abbreviation, 
    SUM(b.hits) as H, SUM(b.home_runs) as HR, SUM(b.at_bats) as AB,
    ROUND(CAST(SUM(b.hits) AS FLOAT) / NULLIF(SUM(b.at_bats), 0), 3) as AVG
  FROM batting_stats b
  JOIN players p ON b.player_id = p.id
  LEFT JOIN teams t ON p.team_id = t.id
  GROUP BY b.player_id
  HAVING SUM(b.at_bats) >= 100
  ORDER BY AVG DESC
  LIMIT 10
""")
print('--- Batting AVG Leaders (min 100 AB) ---')
for r in c.fetchall():
    print(r)

# HR leaders
c.execute("""
  SELECT p.full_name, t.abbreviation, SUM(b.home_runs) as HR
  FROM batting_stats b
  JOIN players p ON b.player_id = p.id
  LEFT JOIN teams t ON p.team_id = t.id
  GROUP BY b.player_id
  ORDER BY HR DESC
  LIMIT 10
""")
print('\n--- HR Leaders ---')
for r in c.fetchall():
    print(r)

# Savant data
c.execute("""
  SELECT p.full_name, s.avg_exit_velocity, s.barrel_rate, s.xba, s.xwoba
  FROM savant_stats s
  JOIN players p ON s.player_id = p.id
  WHERE s.is_pitcher = 0 AND s.avg_exit_velocity IS NOT NULL
  ORDER BY s.avg_exit_velocity DESC
  LIMIT 10
""")
print('\n--- Savant Exit Velo Leaders ---')
for r in c.fetchall():
    print(r)

# ERA Leaders
c.execute("""
  SELECT p.full_name, t.abbreviation,
    SUM(ps.innings_pitched) as IP,
    ROUND(SUM(ps.earned_runs) * 9.0 / NULLIF(SUM(ps.innings_pitched), 0), 2) as ERA,
    SUM(ps.strikeouts) as K
  FROM pitching_stats ps
  JOIN players p ON ps.player_id = p.id
  LEFT JOIN teams t ON p.team_id = t.id
  GROUP BY ps.player_id
  HAVING SUM(ps.innings_pitched) >= 50
  ORDER BY ERA ASC
  LIMIT 10
""")
print('\n--- ERA Leaders (min 50 IP) ---')
for r in c.fetchall():
    print(r)

conn.close()
