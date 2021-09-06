################
# This scripts reads data from the sqlite db into mysql
################
import pandas as pd
import sqlite3
import os
import pymysql
from mysql_config import *

def connectToMySQLDB():
    conn = pymysql.connect(
        host=MYSQL_DATABASE_HOST,
        user=MYSQL_DATABASE_USER,
        password=MYSQL_DATABASE_PASSWORD,
        db=MYSQL_DATABASE_DB,
        cursorclass=pymysql.cursors.DictCursor
    )
    curr = conn.cursor()

    return conn, curr


def connectToSQLiteDB():
    dbname = "databases/monke.db"

    if os.path.exists(dbname):
        return sqlite3.connect(dbname)

    c = sqlite3.connect(dbname)

    return c

c = connectToSQLiteDB()
c.row_factory = sqlite3.Row
curr = c.cursor()

# fstring not safe, but ok since parsed float
query = f"""
SELECT *
FROM Monke
WHERE player_count > 0
AND timestamp >= "2021-03-01"
AND timestamp < "2021-03-10"
ORDER BY timestamp DESC;
"""
curr.execute(query)
recent_updates = [dict(row) for row in curr.fetchall()]
c.close()

df = pd.DataFrame(recent_updates)
df.columns = ['timestamp', 'player_count', 'room_name', 'game_version', 'game_name']
recent_updates = df.to_dict('records')

print(f'Got {len(recent_updates)} rows')



# INSERT
conn, curr = connectToMySQLDB()

index = 0
for row in recent_updates:
    index += 1
    if index % 10000 == 0:
        print(index/len(recent_updates))
        #conn.commit()
    query = """
    INSERT INTO Monke
    (
        timestamp,
        player_count,
        room_name,
        game_version,
        game_name
    )
    VALUES
    (
        %(timestamp)s,
        %(player_count)s,
        %(room_name)s,
        %(game_version)s,
        %(game_name)s
    );
    """
    curr.execute(query, row)
conn.commit()
curr.close()
