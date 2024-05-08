import os
import sys
import json
import time
import requests
import threading
import websocket
from keep_alive import keep_alive

status = "online"  # online/dnd/idle

GUILD_ID = 1234008983518576711
CHANNEL_ID = 1236506554618871818
SELF_MUTE = True
SELF_DEAF = False

usertokens = os.getenv("TOKENS")
if not usertokens:
    print("[ERROR] Please add tokens inside Secrets.")
    sys.exit()

tokens = usertokens.split(',')

headers = {"Content-Type": "application/json"}

def validate_token(token):
    validate = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers={"Authorization": token})
    return validate.status_code == 200

def joiner(token, status, event):
    ws = websocket.WebSocket()
    ws.connect('wss://gateway.discord.gg/?v=9&encoding=json')
    start = json.loads(ws.recv())
    heartbeat_interval = start['d']['heartbeat_interval'] / 1000
    last_heartbeat = time.time()
    auth = {"op": 2, "d": {"token": token, "properties": {"$os": "Windows 10", "$browser": "Google Chrome", "$device": "Windows"}, "presence": {"status": status, "afk": False}}, "s": None, "t": None}
    vc = {"op": 4, "d": {"guild_id": GUILD_ID, "channel_id": CHANNEL_ID, "self_mute": SELF_MUTE, "self_deaf": SELF_DEAF}}
    ws.send(json.dumps(auth))
    ws.send(json.dumps(vc))
    while True:
        if time.time() - last_heartbeat >= heartbeat_interval:
            ws.send(json.dumps({"op": 1, "d": None}))
            last_heartbeat = time.time()
        response = ws.recv()
        if response == "":
            break
    event.set()  # Signal that this thread has finished its task

def run_joiner():
    os.system("clear")
    join_event = threading.Event()  # Event to synchronize joining
    threads = []
    for token in tokens:
        if validate_token(token):
            userinfo = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers={"Authorization": token}).json()
            username = userinfo["username"]
            discriminator = userinfo["discriminator"]
            userid = userinfo["id"]
            print(f"Logged in as {username}#{discriminator} ({userid}).")
            thread = threading.Thread(target=joiner, args=(token, status, join_event))
            threads.append(thread)
            thread.start()
        else:
            print(f"[ERROR] Token {token} might be invalid. Please check it again.")

    # Wait for all threads to finish before proceeding
    for thread in threads:
        thread.join()

    # Once all threads have finished, print a message indicating all accounts have joined
    print("All accounts have joined the voice channel.")

keep_alive()
run_joiner()