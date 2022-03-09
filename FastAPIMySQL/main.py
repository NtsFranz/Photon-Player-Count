from fastapi import FastAPI, Request
from typing import Optional
from fastapi.responses import HTMLResponse
from db import *
import statistics
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import time
from datetime import datetime, timedelta
import random
from pydantic import BaseModel
from fastapi import FastAPI, Form

description = """

"""

limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])
app = FastAPI(
    title="Monke Player Count API",
    description=description,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

origins = [
    "http://localhost:1313",
    "https://metrics.ignitevr.gg",
    "http://ignite-metrics-api.crabdance.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


last_insert = time.time()
insert_interval = .1


class PostData(BaseModel):
    player_count: int
    room_name: str
    game_version: str
    game_name: str


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@limiter.exempt
def read_root(request: Request):
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8"> <!-- Important: rapi-doc uses utf8 charecters -->
  <script type="module" src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"></script>
</head>
<body>
  <rapi-doc
    render-style = "read" 
    primary-color = "#2d6347" 
    show-header = "false" 
    show-info = "true"
    spec-url = "/openapi.json" 
    default-schema-tab = 'example'
    > 

    <div slot="nav-logo" style="display: flex; align-items: center; justify-content: center;"> 
      <img src = "/static/header.jpg" style="width:10em; margin: auto;" />
    </div>
  </rapi-doc>
</body>
</html>"""



@app.get("/how_many_monke_graph")
async def how_many_monke_graph(hours: float = 24):
    """
    Gets an array of historical player counts from the database.
    """

    conn, curr = connectToDB()

    old_hours = []

    # this is the fractional hour up until now
    last_hour = datetime.utcnow().replace(microsecond=0, second=0, minute=0)

    # calculate the new number of hours from this time to the beginning
    start_time = datetime.utcnow() - timedelta(hours=hours)

    for i in range(0, int((last_hour - start_time).total_seconds() / 3600)):
        old_hours.append(last_hour - timedelta(hours=i+1))

    # also add the last fractional bit.
    old_hours.append(start_time)
    old_hours = list(set(old_hours))

    all_data = []
    for old_hour in old_hours:
        all_data.extend(get_data_from_hour(old_hour, conn, curr, True))

    # get the rest of the recent data without cache
    all_data.extend(get_data_from_hour(last_hour, conn, curr, False))

    all_data = sorted(all_data, key=lambda t: t['timestamp'])

    num_values = 1024
    if len(all_data) > num_values:
        all_data = all_data[::int(len(all_data)/num_values)]

    conn.commit()
    curr.close()

    return all_data


@app.get("/how_many_monke")
async def how_many_monke():
    """
    Gets the current player count from the database. returns a median of the last N values. N is around 200 right now.
    """

    conn, curr = connectToDB()

    query = """
    SELECT `player_count`
    FROM `Monke`
    ORDER BY `timestamp` DESC
    LIMIT 200;
    """
    curr.execute(query)
    most_recent_update = [dict(row)['player_count'] for row in curr.fetchall()]
    conn.close()
    median = round(statistics.median(most_recent_update))

    return median


@app.post("/update_monke_count")
@limiter.exempt
def update_monke_count(request: Request, player_count: int = Form(...), room_name: str = Form(...), game_version: str = Form(...), game_name: str = Form(...)):
    """
    Adds a sample of the current player count to the database.
    """
    
    global last_insert

    if time.time() - last_insert < insert_interval:
        return ""

    last_insert = time.time()

    conn, curr = connectToDB()


    if player_count is None:
        return 'No player count', 400

    try:
        data = {
            "player_count": player_count,
            "room_name": room_name,
            "game_version": game_version,
            "game_name": game_name,
        }
    except:
        return "ur a failure"

    query = """
    INSERT INTO Monke
    (
        player_count
    )
    VALUES
    (
        %(player_count)s
    );
    """
    curr.execute(query, data)
    conn.commit()
    curr.close()
    return "Success"

