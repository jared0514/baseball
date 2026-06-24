import sqlite3
conn = sqlite3.connect('data/mlb.db')
c = conn.cursor()

al_east = [147, 110, 111, 139, 141]
al_cent = [116, 118, 114, 142, 145]
al_west = [117, 136, 140, 108, 133]

nl_east = [143, 144, 121, 120, 146]
nl_cent = [158, 112, 113, 138, 134]
nl_west = [119, 135, 109, 137, 115]

for mlb_id in al_east: c.execute('UPDATE teams SET league="AL", division="East" WHERE mlb_id=?', (mlb_id,))
for mlb_id in al_cent: c.execute('UPDATE teams SET league="AL", division="Central" WHERE mlb_id=?', (mlb_id,))
for mlb_id in al_west: c.execute('UPDATE teams SET league="AL", division="West" WHERE mlb_id=?', (mlb_id,))

for mlb_id in nl_east: c.execute('UPDATE teams SET league="NL", division="East" WHERE mlb_id=?', (mlb_id,))
for mlb_id in nl_cent: c.execute('UPDATE teams SET league="NL", division="Central" WHERE mlb_id=?', (mlb_id,))
for mlb_id in nl_west: c.execute('UPDATE teams SET league="NL", division="West" WHERE mlb_id=?', (mlb_id,))

conn.commit()
print('Teams updated!')
