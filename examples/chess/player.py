import weave


@weave.type()
class Player:
    @weave.op()
    async def move(self, board_fen: str) -> str:
        ...
