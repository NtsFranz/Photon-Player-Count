################
# This scripts reads data from the mysql db
# and filters it with 1 row per minute
################
import pandas as pd
import os
from datetime import datetime, timedelta
import math
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



def get_data_from_hour(hour_timestamp, conn, curr, should_add_to_cache: bool):



    # fetch from big boy database
    query = f"""
    SELECT `timestamp`, `player_count`
    FROM `Monke`
    WHERE `timestamp` >= '{hour_timestamp}'
    AND `timestamp` < '{hour_timestamp+timedelta(hours=1)}'
    ORDER BY `timestamp` DESC;
    """
    curr.execute(query)
    output = [dict(row) for row in curr.fetchall()]

    if len(output) == 0:
        return pd.DataFrame()
    
    # add the data to a dataframe
    df = pd.DataFrame(output)
    df.columns = ['timestamp', 'player_count']
    df['player_count'] = pd.to_numeric(df['player_count'], errors='coerce')
    df = df.dropna()
    
    filtered_df = pd.DataFrame()

    # loop through the 60 minutes in this hour and get the median of each
    minute_list = [hour_timestamp + timedelta(minutes=x) for x in range(60)]
    for m in range(0, len(minute_list)):
        this_minute_df = df.loc[df['timestamp'] >= minute_list[m]]
        this_minute_df = this_minute_df.loc[this_minute_df['timestamp'] < minute_list[m] + timedelta(minutes=1)]

        median = this_minute_df['player_count'].median()
        # print(f'{median = }')
        if not math.isnan(median):
            filtered_df = filtered_df.append({
                'timestamp': minute_list[m],
                'player_count': median
            }, ignore_index = True)


    for i in range (0, 4):
        filtered_df = filtered_df[filtered_df['player_count'] > filtered_df['player_count'].shift(-1) - 200]
        filtered_df = filtered_df[filtered_df['player_count'] < filtered_df['player_count'].shift(-1) + 200]

    return filtered_df






csv_name = 'one_per_minute_mysql.csv'
if os.path.exists(csv_name):
    output_df = pd.read_csv(csv_name)
else:
    output_df = pd.DataFrame()

conn, curr = connectToMySQLDB()
base = datetime.strptime('2021-09-06', '%Y-%m-%d')
minute_list = [base - timedelta(minutes=x) for x in range(1000000)]
had_data_once = False
for i in range(0, len(minute_list)):


    # fetch from big boy database
    query = f"""
    SELECT `timestamp`, `player_count`
    FROM `Monke`
    WHERE `timestamp` >= '{minute_list[i]}'
    AND `timestamp` < '{minute_list[i]+timedelta(minutes=1)}'
    ORDER BY `timestamp` DESC;
    """
    curr.execute(query)
    output = [dict(row) for row in curr.fetchall()]

    if len(output) > 0:
        had_data_once = True
    else:
        continue

    # add the data to a dataframe
    df = pd.DataFrame(output)
    df.columns = ['timestamp', 'player_count']
    df['player_count'] = pd.to_numeric(df['player_count'], errors='coerce')
    df = df.dropna()

    median = df['player_count'].median()
    # print(f'{median = }')
    if not math.isnan(median):
        output_df = output_df.append({
            'timestamp': minute_list[i],
            'player_count': median
        }, ignore_index = True)

    print(f'{minute_list[i]:%Y-%m-%d %H-%M}\t{len(output)}\t{len(output_df)}')

    if i % 1000 == 0:
        
        print(f'{len(output_df) = :.0f}')
        output_df.to_csv(csv_name)
        break

output_df.to_csv(csv_name)
curr.close()