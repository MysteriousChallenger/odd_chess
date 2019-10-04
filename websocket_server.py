
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

# this storage system isn't even close to efficient. Whatever


class Game:
    def __init__(self, players=None, spectators=set(), playermax=2, id=-1):
        if players == None:
            self.players = [None]*playermax
        else:
            self.players = players
        self.spectators = spectators
        self.playermax = playermax
        self.playercount = len(list(player for player in self.players if player != None))
        self.turn = random.randint(0, 1)
        self.last_move = {'msg_type': 'reset'}
        if id == -1:
            self.id = gen_uuid()
        else:
            self.id = id

    def __lt__(self, other):
        return self.id < other.id

    def __gt__(self, other):
        return self.id > other.id

    def __eq__(self, other):
        if other == None:
            return False
        return self.id == other.id

    def add_user(self, websocket, random = False):
        if len(self.players) < self.playermax:
            if random == False:
                for i in range(len(self.players)):
                    if self.players[i] == None:
                        self.players[i] = websocket
                        break
            else:
               player_position = random.randint(self.max_players - self.playercount)
               for i in range(len(self.players)):
                   if self.players[i] == None:
                        player_position -= 1
                        if player_position == 0:
                            self.players[i] = websocket
            return True
        else:
            self.spectators.add(websocket)
            return False

    def is_turn(self, websocket):
        for i in range(len(self.players)):
            if self.players[i] == websocket:
                if self.turn % self.playermax == i:
                    return True
        return False

    def remove_user(self, websocket):
        try:
            playerindex = self.players.index(websocket)
            if playerindex == -1:
                return
            else:
                self.players[playerindex] = None
        except ValueError:
            self.spectators.discard(websocket)


def gen_uuid():
    current_time = time.time()
    return int(current_time * 2**math.frexp(current_time)[1]) % 10**12


async def connection_handler(websocket, path):
    global next_open_game
    if path == "/websockets/game":  # manage games websockets
        game = None
        game_index = -1
        game_started = False

        def create_and_register_game_and_user(websocket):
            global games
            game = Game(players=list((websocket,)))
            index = bisect.bisect_left(games, game)
            games.insert(index, game)
            return (game, index)

        def unregister_user(game, websocket):
            game.remove_user(websocket)

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
                        game, game_index = create_and_register_game_and_user(
                            websocket)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " creating new game "+str(
                            game.id)+". total: " + str(len(games)))
                        next_open_game = game
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init", "result": "success", "game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket)}))
                    else:
                        game, game_index = locate_game(next_open_game.id)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " connecting to game " + str(
                            game.id) + ". total: " + str(len(games)+1))
                        game.add_user(websocket)
                        if len(game.players) >= game.playermax:
                            next_open_game = None
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init", "result": "success", "game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket)}))
                elif data["game_init"] == "private":
                    if data["game_id"] == -1:
                        game, game_index = create_and_register_game_and_user(
                            websocket)
                        logging.info("WS:"+str(websocket.remote_address[0]) + " creating new game "+str(
                            game.id)+". total: " + str(len(games)))
                        game_started = True
                        await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket)}))
                    else:
                        game, game_index = locate_game(data["game_id"])
                        if game == None:
                            logging.info("WS:"+str(websocket.remote_address[0]) + " failed to connect to game " + str(data["game_id"]) + ". total: " + str(len(games)))
                            await websocket.send(json.dumps({"msg_type": "game_init","result":"error","error":"game not found"}))
                        else:
                            logging.info("WS:"+str(websocket.remote_address[0]) + " connecting to game " + str(data["game_id"]) + ". total: " + str(len(games)+1))
                            is_player = game.add_user(websocket)
                            game_started = True
                            if is_player:
                                await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": True, "is_turn": game.is_turn(websocket)}))
                                if len(game.players) >= game.playermax:
                                    next_open_game = None
                            else:
                                await websocket.send(json.dumps({"msg_type": "game_init","result":"success","game_id": game.id, "is_player": False, "is_turn": game.is_turn(websocket)}))
                                await websocket.send(game.last_move)
            async for message in websocket:
                print(message)
                if game.is_turn(websocket):
                    game.last_move = message
                    game.turn += 1
                    for i in game.players:
                        if i != websocket:
                            await i.send(message)
                    for i in game.spectators:
                        await i.send(message)
                else:
                    await websocket.send(game.last_move)
        finally:
            if(game != None):
                unregister_user(game, websocket)
                if len(game.players) == 0:
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
            connection_handler, host="localhost", port=80)
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()
    t = Thread(target=startscript)
    t.start()
