import asyncio
import logging
import re
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.session import StringSession

from .utils import normalize_word, random_delay
from .words import load_words


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WordSolver:

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        string_session: str,
        owner_id: int,
        speed: float = 5.0,
        bot_username: str = "WordSeekBot"
    ):

        self.owner_id = owner_id
        self.speed = speed
        self.bot_username = bot_username

        self.ALL_WORDS, self.COMMON_WORDS = load_words()

        self.app = Client(
            StringSession(string_session),
            api_id=api_id,
            api_hash=api_hash
        )

        self.game_state = {}

        self._register_handlers()

    # ─────────────────────────
    # Speed Control
    # ─────────────────────────
    def set_speed(self, seconds: float):
        self.speed = seconds

    # ─────────────────────────
    # Word Logic
    # ─────────────────────────
    def _get_next_word(self, chat_id):
        state = self.game_state.get(chat_id)
        if not state:
            return None

        remaining = list(state["possible_words"] - state["used_words"])
        if not remaining:
            return None

        word = remaining[0]
        state["used_words"].add(word)
        return word

    async def _send_guess(self, message, word):
        await asyncio.sleep(random_delay(self.speed))
        state = self.game_state[message.chat.id]
        state["last_guess"] = word
        state["last_time"] = datetime.now()
        await message.reply(word.upper())

    # ─────────────────────────
    # Handlers
    # ─────────────────────────
    def _register_handlers(self):

        @self.app.on_message(filters.command("game") & filters.group)
        async def start_game(_, message):
            if message.from_user.id != self.owner_id:
                return

            self.game_state[message.chat.id] = {
                "active": True,
                "possible_words": set(self.ALL_WORDS),
                "used_words": set(),
                "last_guess": None
            }

            await message.reply("🤖 Word Solver Activated")

        @self.app.on_message(filters.command("sleep") & filters.group)
        async def stop_game(_, message):
            if message.from_user.id != self.owner_id:
                return

            self.game_state.pop(message.chat.id, None)
            await message.reply("😴 Solver Deactivated")

        @self.app.on_message(filters.command("speed") & filters.group)
        async def change_speed(_, message):
            if message.from_user.id != self.owner_id:
                return

            try:
                value = float(message.command[1])
                self.set_speed(value)
                await message.reply(f"⚡ Speed set to {value}s")
            except:
                await message.reply("Usage: /speed 3")

        @self.app.on_message(filters.group & filters.text)
        async def bot_handler(_, message):

            if not message.from_user:
                return

            if message.from_user.username != self.bot_username:
                return

            state = self.game_state.get(message.chat.id)
            if not state:
                return

            text = message.text.lower()

            # Game start detection
            if "game started" in text:
                word = self._get_next_word(message.chat.id)
                if word:
                    await self._send_guess(message, word)

            # Win detection
            if "congrats" in text or "correct word" in text:
                await message.reply("/new")

    # ─────────────────────────
    # Run
    # ─────────────────────────
    def run(self):
        print("🚀 Word Solver Running...")
        self.app.run()