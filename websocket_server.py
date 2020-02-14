
import asyncio
import websockets
import json
from threading import Thread
import time
import math
import bisect
from types import SimpleNamespace
import logging
import random
import os
import ssl

# this storage system isn't even close to efficient. Whatever


class Game:
    def __init__(self, players=None, spectators=set(), playermax=2, id=-1):
        if players == None:
            self.playercount = 0
            self.players = [None]*playermax
        else:
            self.playercount = len(list(player for player in self.players if player != None))
            self.players = players
        self.spectators = spectators
        self.playermax = playermax
        self.turn = random.randint(0, 1)
        self.last_move = '{"msg_type": "reset"}'
        if id == -1:
            self.id = gen_uuid()
        else:
            self.id = id
        print("pp pl", self.playercount)

    def __lt__(self, other):
        return self.id < other.id

    def __gt__(self, other):
        return self.id > other.id

    def __eq__(self, other):
        if other == None:
            return False
        return self.id == other.id

    async def add_user(self, websocket, random_order = True):
        if self.playercount < self.playermax:
            self.playercount += 1
            if random_order == False:
                for i in range(len(self.players)):
                    if self.players[i] == None:
                        self.players[i] = websocket
                        break
            else:
               player_position = random.randint(0,self.playermax - self.playercount)
               for i in range(len(self.players)):
                   if self.players[i] == None:
                        player_position -= 1
                        if player_position <= -1:
                            self.players[i] = websocket
                            break
            print("add_user",self.players)
            for i in self.players:
                if i != None and i != websocket :
                    await i.send(json.dumps({"msg_type":"game_playercount_update", "game_playercount":self.playercount}))
            return True
        else:
            self.spectators.add(websocket)
            return False

    def is_turn(self, websocket):
        print("is_turn",self.players)
        if self.players[self.turn%self.playermax] == websocket:
            return True
        else:
            return False

    async def remove_user(self, websocket):
        try:
            playerindex = self.players.index(websocket)
            if playerindex == -1:
                print("nouser")
                return
            else:
                self.players[playerindex] = None
                self.playercount -= 1
                print("user removed, pcount", self.playercount)
                for i in self.players:
                    if i != None and i != websocket :
                        await i.send(json.dumps({"msg_type":"game_playercount_update", "game_playercount":self.playercount}))
        except ValueError:
            self.spectators.discard(websocket)

def gen_uuid():
    current_time = time.time()
    return int(current_time * 2**math.frexp(current_time)[1]) % 10**12

#THIS IS AWFUL. started small and somehow grew really really big
#todo compartmentalize into smaller functions
async def connection_handler(websocket, path):
    global next_open_game
    if path == "/websockets/game":  # manage games websockets
        game = None
        game_index = -1
        game_started = False

        async def create_and_register_game_and_user(websocket):
            global games
            game = Game(playermax=2)
            await game.add_user(websocket)
            index = bisect.bisect_left(games, game)
            games.insert(index, game)
            return (game, index)

        async def unregister_user(game, websocket):
            await game.remove_user(websocket)

        def unregister_game(index):
            del games[index]

        def locate_game(game_id):
            index = bisect.bisect_left(games, Game(id=game_id))
            if index != len(games) and game_id == games[index].id:
                return (games[index], index)
            else:
                return(None, -1)
        try:
            while(game_started == False):
                message = await websocket.recv()
                print(message)
                data = json.loads(message)
                if data["game_init"] == "random":
                    if next_open_game == None:
                        game, game_index = await create_and_register_game_and_user(
                            websocket)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " creating new game "+str(
                            game.id)+". total: " + str(len(games)))
                        next_open_game = game
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init", "result": "success", "game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket), "game_playercount": game.playercount, "last_move": game.last_move}))
                    else:
                        game, game_index = locate_game(next_open_game.id)
                        print("connecting nextopengame", game, game_index)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " connecting to game " + str(
                            game.id) + ". total: " + str(len(games)+1))
                        await game.add_user(websocket)
                        if len(game.players) >= game.playermax:
                            next_open_game = None
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init", "result": "success", "game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket), "game_playercount": game.playercount , "last_move": game.last_move}))

                elif data["game_init"] == "private":
                    if data["game_id"] == -1:
                        game, game_index = await create_and_register_game_and_user(
                            websocket)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " creating new game "+str(
                            game.id)+". total: " + str(len(games)))
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket), "game_playercount": game.playercount,  "last_move": game.last_move}))
                    else:
                        game, game_index = locate_game(data["game_id"])
                        if game == None:
                            logging.info("WS:"+str(websocket.remote_address[0]) + " failed to connect to game " + str(data["game_id"]) + ". total: " + str(len(games)))
                            await websocket.send(json.dumps({"msg_type": "game_init","result":"error","error":"game not found"}))
                        else:
                            logging.info("WS:"+str(websocket.remote_address[0]) + " connecting to game " + str(data["game_id"]) + ". total: " + str(len(games)))
                            is_player = await game.add_user(websocket,random_order = False)
                            game_started = True
                            if is_player:
                                if len(game.players) >= game.playermax:
                                    next_open_game = None
                                await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket), "game_playercount": game.playercount, "last_move": game.last_move}))
                            else:
                                await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": False, "is_turn": game.is_turn(websocket), "game_playercount": game.playercount, "last_move": game.last_move}))
            async for message in websocket:
                print(message, game.is_turn(websocket), game.players)
                if game.is_turn(websocket):
                    game.last_move = message
                    game.turn += 1
                    for i in game.players:
                        if i != None and i != websocket :
                            await i.send(message)
                    for i in game.spectators:
                        await i.send(message)
                else:
                    time.sleep(0.3)
                    await websocket.send(game.last_move)
        finally:
            if(game != None):
                await unregister_user(game, websocket)
                if game.playercount <= 0:
                    if game == next_open_game:
                        next_open_game = None
                    unregister_game(game_index)
                    logging.info("WS:"+str(websocket.remote_address[0]) + " leaves game " + str(game.id) + ". total: " + str(len(games)))
                    

games = []
next_open_game = None
logging.basicConfig(
    format='%(asctime)s  %(message)s',
    level=logging.INFO,
    datefmt='[%d/%b/%Y %H:%M:%S]')


def launch_server():
    def startscript():
        print("launching websocket server")
        asyncio.set_event_loop(asyncio.new_event_loop())
        server = websockets.serve(
            connection_handler, host="0.0.0.0", port=int(os.environ.get("PORT", 80)))
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()
    t = Thread(target=startscript)
    t.start()
