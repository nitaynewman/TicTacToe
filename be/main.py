from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from uuid import uuid4
import asyncio

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


games = {}

class Game:
    def __init__(self):
        self.board = [""] * 9
        self.players = []
        self.turn = "X"  
        self.winner = None

    async def send_state(self):
        """Send game state to both players."""
        state = {"board": self.board, "turn": self.turn, "winner": self.winner}
        for player in self.players:
            await player.send_json(state)

    def make_move(self, index, symbol):
        """Validate and make a move."""
        if self.board[index] == "" and self.turn == symbol and not self.winner:
            self.board[index] = symbol
            self.turn = "O" if self.turn == "X" else "X"
            self.check_winner()
            return True
        return False

    def check_winner(self):
        """Check if there's a winner."""
        win_patterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  
            [0, 4, 8], [2, 4, 6]            
        ]
        for pattern in win_patterns:
            a, b, c = pattern
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]

@app.get("/create-game")
def create_game():
    """Create a new game and return its ID."""
    game_id = str(uuid4())
    games[game_id] = Game()
    return {"game_id": game_id}

@app.websocket("/ws/{game_id}/{symbol}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, symbol: str):
    """Handle WebSocket connections for players."""
    await websocket.accept()

    if game_id not in games:
        await websocket.close()
        return

    game = games[game_id]

    if len(game.players) >= 2:
        await websocket.close()
        return

    game.players.append(websocket)

    if len(game.players) == 2:
        await game.send_state()

    try:
        while True:
            data = await websocket.receive_json()
            index = data["index"]

            if game.make_move(index, symbol):
                await game.send_state()
    except WebSocketDisconnect:
        game.players.remove(websocket)
