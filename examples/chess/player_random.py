import weave
import random
import chess

from player import Player


@weave.type()
class RandomPlayer(Player):
    @weave.op()
    async def move(self, board_fen: str) -> str:
        import chess
        import random

        board = chess.Board(board_fen)
        return random.choice(list(board.legal_moves)).uci()
