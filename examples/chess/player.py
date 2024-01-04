import weave


@weave.type()
class Player:
    @weave.op()
    def move(self, board_fen: str) -> str:
        ...
