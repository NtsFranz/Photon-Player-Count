################
# This scripts reads data from the sqlite db 
# and filters it with 1 row per minute
################
import pandas as pd
import sqlite3
import os
import datetime
import math


def connectToSQLiteDB():
    dbname = "databases/monke.db"

    if os.path.exists(dbname):
        return sqlite3.connect(dbname)

    c = sqlite3.connect(dbname)

    return c



csv_name = 'one_per_minute.csv'
if os.path.exists(csv_name):
    filtered_df = pd.read_csv(csv_name)
else:
    filtered_df = pd.DataFrame()

base = datetime.datetime.strptime('2021-07-19', '%Y-%m-%d')
date_list = [base - datetime.timedelta(days=x) for x in range(1000)]
still_has_data = True
had_data_once = False
for i in range(0, len(date_list)):

    print('')
    print(f'{date_list[i+1] = :%Y-%m-%d}')
    print(f'{date_list[i]   = :%Y-%m-%d}')

    
    c = connectToSQLiteDB()
    c.row_factory = sqlite3.Row
    curr = c.cursor()

    # fstring not safe, but ok since parsed float
    query = f"""
    SELECT *
    FROM Monke
    WHERE player_count > 0
    AND timestamp >= "{date_list[i+1]}"
    AND timestamp < "{date_list[i]}"
    ORDER BY timestamp DESC;
    """
    curr.execute(query)
    recent_updates = [dict(row) for row in curr.fetchall()]
    c.close()

    print(f'Got {len(recent_updates):.0f} rows')

    if len(recent_updates) > 0:
        had_data_once = True
    elif had_data_once:
        break
    else:
        continue

    cols = ['timestamp', 'player_count', 'room_name', 'game_version', 'game_name']
    df = pd.DataFrame(recent_updates)
    df.columns = cols
    df = df[['timestamp', 'player_count']]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['player_count'] = pd.to_numeric(df['player_count'], errors='coerce')
    df = df.dropna()

    minute_list = [date_list[i+1] + datetime.timedelta(minutes=x) for x in range(1440)]
    for m in range(0, len(minute_list)):
        this_minute_df = df.loc[df['timestamp'] >= minute_list[m]]
        this_minute_df = this_minute_df.loc[this_minute_df['timestamp'] < minute_list[m] + datetime.timedelta(minutes=1)]

        median = this_minute_df['player_count'].median()
        # print(f'{median = }')
        if not math.isnan(median):
            filtered_df = filtered_df.append({
                'timestamp': minute_list[m],
                'player_count': median
            }, ignore_index = True)

    print(f'{len(filtered_df) = :.0f}')
    filtered_df.to_csv(csv_name)

