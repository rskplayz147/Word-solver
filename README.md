# Word Solver

Telegram WordSeek Auto Solver Userbot

## Install

pip install word-solver

## Usage

```python
from solver import WordSolver

solver = WordSolver(
    api_id=12345,
    api_hash="API_HASH",
    string_session="STRING_SESSION",
    owner_id=123456789,
    speed=5
)

solver.run()