import operator
from flask import Flask, escape, request, jsonify, render_template, abort
import requests
import sqlite3
import json
import os
import datetime

app = Flask(__name__)

def connectToMonkeDB():
    dbname = "monke.db"

    if os.path.exists(dbname):
        return sqlite3.connect(dbname)

    c = sqlite3.connect(dbname)

    try:
        c.executescript('''
        DROP TABLE IF EXISTS Monke;
        ''')

        # CREATE DATABASE
        c.executescript('''
        CREATE TABLE `Monke` (
        `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `player_count` INTEGER NOT NULL DEFAULT 0,
        `room_name` TEXT NOT NULL,
        `game_version` TEXT NOT NULL,
        `game_name` TEXT NOT NULL
        );
        ''')

        c.executescript('''
        CREATE INDEX idx_timestamp 
        ON Monke (timestamp);
        ''')
        
        print('Created DB')
    except sqlite3.Error as e:
        c.close()
        print(e)


    return c

@app.route('/update_monke_count', methods=["POST"])
def update_monke_count():
    c = connectToMonkeDB()

    curr = c.cursor()
    
    data = {
        "player_count": request.values.get("player_count", 0),
        "room_name": request.values.get("room_name", "none"),
        "game_version": request.values.get("game_version", "none"),
        "game_name": request.values.get("game_name", "none"),
    }

    query = """
    INSERT INTO Monke
    (
        player_count,
        room_name,
        game_version,
        game_name
    )
    VALUES
    (
        :player_count,
        :room_name,
        :game_version,
        :game_name
    );
    """
    curr.execute(query, data)
    c.commit()
    c.close()

    return "Success"

@app.route('/how_many_monke_graph', methods=["GET"])
def how_many_monke_graph():
    hours = request.args.get('hours', 24)
    try:
        hours = float(hours)
    except:
        print("Failed to parse hours arg. Just using 24")
        hours = 24
    c = connectToMonkeDB()
    c.row_factory = sqlite3.Row
    curr = c.cursor()

    # fstring not safe, but ok since parsed float
    query = f"""
    SELECT *
    FROM Monke
    WHERE timestamp > DATE('now','{-hours} hours')
    ORDER BY timestamp DESC;
    """
    curr.execute(query)
    most_recent_update = [dict(row) for row in curr.fetchall()]
    c.close()

    return jsonify(most_recent_update)

@app.route('/how_many_monke', methods=["GET"])
def how_many_monke():
    c = connectToMonkeDB()
    c.row_factory = sqlite3.Row
    curr = c.cursor()

    query = """
    SELECT *
    FROM Monke
    ORDER BY timestamp DESC
    LIMIT 1;
    """
    curr.execute(query)
    most_recent_update = [dict(row) for row in curr.fetchall()]
    c.close()
    if len(most_recent_update) == 0:
        return 'No monke yet'
    most_recent_update = most_recent_update[0]


    return jsonify(most_recent_update)