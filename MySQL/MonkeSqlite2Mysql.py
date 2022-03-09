################
# This scripts reads data from the sqlite db into mysql
################
import pandas as pd
import sqlite3
import os
import pymysql
import datetime
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


base = datetime.datetime.strptime('2021-03-08', '%Y-%m-%d')
date_list = [base - datetime.timedelta(days=x) for x in range(1000)]
still_has_data = True
had_data_once = False
for i in range(0, len(date_list)):

    print('')
    print(f'{date_list[i+1]=:%Y-%m-%d}')
    print(f'{date_list[i]  =:%Y-%m-%d}')

    c = connectToSQLiteDB()
    c.row_factory = sqlite3.Row
    curr = c.cursor()

    # fstring not safe, but ok since parsed float
    query = f"""
    SELECT *
    FROM Monke
    WHERE player_count > 0
    AND timestamp >= "{date_list[i+1]}"
    AND timestamp < "{date_list[i]}";
    """
    curr.execute(query)
    recent_updates = [dict(row) for row in curr.fetchall()]
    c.close()

    print(f'Got {len(recent_updates)} rows')

    if len(recent_updates) > 0:
        had_data_once = True
    elif had_data_once:
        break
    else:
        continue

    df = pd.DataFrame(recent_updates)
    df.columns = ['timestamp', 'player_count', 'room_name', 'game_version', 'game_name']
    df['player_count'] = pd.to_numeric(df['player_count'], errors='coerce')
    df = df.loc[df['player_count'] < 100000]
    df = df.dropna()
    recent_updates = df.to_dict('records')




    # INSERT
    conn, curr = connectToMySQLDB()

    index = 0
    for row in recent_updates:
        index += 1
        if index % 10000 == 0:
            print(f'{index/len(recent_updates)*100:.0f}%')
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
        try:
            curr.execute(query, row)
        except:
            print(curr._last_executed)
            raise
        
    conn.commit()
    curr.close()

