import discord
import requests
import json
import sys
import math
import os
import sqlite3
import sched
import time
from discord.ext import tasks
from asyncio import sleep
import traceback
import asyncio
from fuzzywuzzy import fuzz
import pandas as pd
import matplotlib.pyplot as plt


from datetime import datetime

from discord_bot_config import *



client = discord.Client()

s = sched.scheduler(time.time, time.sleep)

rename_channels = [
    {
        "server": 706393774804303924,
        "channel": 706393776918364211
    },
    {
        "server": 671854243510091789,
        "channel": 716146011466104902
    }
]

last_channel_name = "none"


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # don't respond to our own messages
    if message.author == client.user:
        return

    # don't listen for messages if we're just trying to edit the channel name
    if len(sys.argv) > 1 and sys.argv[1] == "edit_channel_only":
        return

    # possibly restrict to testing channel
    if debug and message.channel.id != debugChannel:
        return

    # old usercount command without graph
    if message.content == '!usercount':
        store_in_db(message)

        data = get_user_count()

        await post_message(
            data['player_count'],
            version=data["game_version"],
            room=data["room_name"],
            channel=message.channel)

    # show cool graph
    if fuzz.ratio(message.content.lower(), 'howmanymonke') > 70:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True)

        await post_graph(pd.DataFrame(data), message, "Last 24 hours:")

    # show cool graph for longer history
    elif fuzz.ratio(message.content.lower(), 'shortmonke') > 90:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True, graph_hours=6)

        await post_graph(pd.DataFrame(data), message, "Last 6 hours:")

    elif fuzz.ratio(message.content.lower(), 'shortshortmonke') > 90:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True, graph_hours=0.5)

        await post_graph(pd.DataFrame(data), message, "Last 30 minutes:")

    # show cool graph for longer history
    elif fuzz.ratio(message.content.lower(), 'longmonke') > 90:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True, graph_hours=96)

        await post_graph(pd.DataFrame(data), message, "Last 4 days:")

    # show cool graph for longer history
    elif fuzz.ratio(message.content.lower(), 'longlongmonke') > 90:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True, graph_hours=168)

        await post_graph(pd.DataFrame(data), message, "Last 7 days:")
    
    # show cool graph for longer history
    elif fuzz.ratio(message.content.lower(), 'longlonglongmonke') > 90:
        store_in_db(message)

        await message.channel.trigger_typing()
        data = get_user_count(graph=True, graph_hours=336)

        await post_graph(pd.DataFrame(data), message, "Last 14 days:")


async def post_message(count, channel, version=None, room=None):
    e = discord.Embed.from_dict({
        "title": "Player Count: " + str(count),
        "description": "Application version: " + str(version) + "\nRoom name: " + str(room),
        # "timestamp": str(datetime.utcnow())
    })
    await channel.send(embed=e)


async def post_graph(df, message, length_message, scatter=False):
    if len(df) > 0:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.columns = ['Time', 'Player Count']

        params = {"ytick.color": "w",
                  "xtick.color": "w",
                  "axes.labelcolor": "w",
                  "axes.edgecolor": "w"}
        plt.rcParams.update(params)
        fig = plt.figure(figsize=(7, 3), dpi=200)
        ax = plt.axes()
        plt.margins(x=0)

        if scatter:
            plt.scatter(x=df['Time'], y=df['Player Count'], alpha=.1, s=.5, c='w')
        else:
            df.plot(ax=ax, x='Time', y='Player Count', linewidth=3.0, c='w')
            ax.get_legend().remove()

        ax.get_xaxis().set_visible(False)
        ax.get_legend().remove()

        plt.savefig('graph.png', transparent=True, bbox_inches='tight')
        plt.draw()
        plt.clf()
        plt.close("all")

        await message.channel.send(content=f"Player Count: **{str(df.iloc[0]['Player Count'])}**\n{length_message}", file=discord.File('graph.png'))
    else:
        await message.channel.send('No monke :(')


async def change_channel_names():
    global last_channel_name
    for c in rename_channels:
        channel = client.get_guild(c['server']).get_channel(c['channel'])
        print("Editing channel name...")
        await channel.edit(name=last_channel_name)
        print("success")


def get_user_count(graph=False, graph_hours=24):
    if graph:
        r = requests.get(monke_graph_url, params={'hours': graph_hours})
    else:
        r = requests.get(monke_count_url)

    if r.status_code != 200:
        return -1
    else:
        return json.loads(r.text)


@tasks.loop(seconds=20)
async def get_user_count_and_post():
    global last_channel_name
    if client is None:
        return
    try:
        data = get_user_count()
        count = data['player_count']
        version = data['game_version']
        room = data['room_name']
        channel_name = "users-online-" + str(count)
        if last_channel_name != channel_name:
            print("")
            print(datetime.now())
            print(channel_name)
            last_channel_name = channel_name

            if len(sys.argv) > 1 and sys.argv[1] == "edit_channel_only":
                await change_channel_names()
            else:
                await post_message(count, version=version, room=room, edit=True)

        # else:
        #     print("no change needed")
    except:
        print('Client not initialized yet.')
        traceback.print_exc()


def create_db_if_not_exists(dbname):
    if os.path.exists(dbname):
        return sqlite3.connect(dbname)

    c = sqlite3.connect(dbname)

    try:
        c.executescript('''
        DROP TABLE IF EXISTS Query;
        ''')

        # CREATE DATABASE
        c.executescript('''
        CREATE TABLE `Query` (
        `id` INTEGER NOT NULL,
        `time` datetime NOT NULL,
        `command_name` TEXT NOT NULL,
        `query_text` TEXT NOT NULL,
        `full_text` TEXT NOT NULL,
        `user` TEXT NOT NULL,
        `server` TEXT NOT NULL,
        `channel` TEXT NOT NULL
        );
        ''')

        c.executescript("PRAGMA foreign_keys = ON;")

    except sqlite3.Error as e:
        c.close()
        print(e)

    return c


def store_in_db(message):

    # try:
    command_name = message.content.split()[0]
    query_text = message.content[len(command_name) + 1:]
    # finally:
    #     command_name = ""
    #     query_text = ""

    data = {
        "id": message.id,
        "time": message.created_at,
        "command_name": command_name,
        "query_text": query_text,
        "full_text": message.content,
        "user": message.author.name,
        "server": message.guild.name,
        "channel": message.channel.name
    }

    query = """
    INSERT INTO Query
    VALUES(
        :id,
        :time,
        :command_name,
        :query_text,
        :full_text,
        :user,
        :server,
        :channel
    )
    """
    c = create_db_if_not_exists("bot_log.db")
    curr = c.cursor()
    curr.execute(query, data)
    c.commit()
    c.close()

# get_user_count_and_post.start()


client.run(discord_client_id)
