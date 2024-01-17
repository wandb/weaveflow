import weave
import random
import chess
from weave.weaveflow import Model


@weave.type()
class RandomPlayer(Model):
    @weave.op()
    async def predict(self, board_fen: str) -> str:
        board = chess.Board(board_fen)
        return random.choice(list(board.legal_moves)).uci()
