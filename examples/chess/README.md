# Chess playing example

Ensure you have the latest version of Weave installed

```
pip install --upgrade weave
```

Then, create a dataset of chess board positions. This uses the stockfish chess engine to score each potential move, storing the move scores alongside the board positions.

By default this only creates 10 examples in the dataset. If you want to really experiment with predicting chess moves, I'd suggest a dataset of 150 examples or more, to get low variance in the evaluated scores.

```
python make_dataset.py
```

Next, evaluate a model.

```
OPENAI_API_KEY=... python evaluate.py
```

Ideas
- You can modify the code in the __main__ of evaluate.py to change the model's system prompt
- You can modify the code in player_llm.py if you want to change how the model works (or copy it to a new class and modify that)