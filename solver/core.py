import asyncio
import logging
import random
import re
import unicodedata
from datetime import datetime

from pyrogram import Client, filters

from .utils import normalize_word, random_delay
from .words import load_words


class WordSolver:

    WORDSEEK_USERNAME = "WordSeekBot"

    def __init__(self, api_id, api_hash, string_session, owner_id, speed=2):

        self.owner_id = owner_id
        self.speed = speed

        self.app = Client(
            "WordSolver",
            api_id=api_id,
            api_hash=api_hash,
            session_string=string_session
        )

        self.ALL_WORDS, _ = load_words()

        self.game_state = {}

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("WordSolver")

        self._register_handlers()

    # ───────── NORMALIZE FONT ─────────
    def normalize_font(self, text):
        return unicodedata.normalize("NFKD", text)

    # ───────── FILTER WORDS ─────────
    def filter_words(self, words, guess, emojis):

        result = set()

        for w in words:

            ok = True

            for i, (g, e) in enumerate(zip(guess, emojis)):

                if e == "🟩" and w[i] != g:
                    ok = False

                elif e == "🟨" and (g not in w or w[i] == g):
                    ok = False

                elif e == "🟥" and g in w:
                    ok = False

            if ok:
                result.add(w)

        return result

    # ───────── NEXT WORD ─────────
    def get_next_word(self, chat_id):

        st = self.game_state.get(chat_id)

        if not st:
            return None

        choices = list(st["possible_words"] - st["used_words"])

        if not choices:
            return None

        word = random.choice(choices)

        st["used_words"].add(word)

        return word

    # ───────── PARSE FEEDBACK ─────────
    def parse_feedback_line(self, line):

        emojis = re.findall(r"[🟩🟨🟥]", line)

        if len(emojis) != 5:
            return None, None

        match = re.search(r"([A-Za-z]{5})$", self.normalize_font(line))

        if not match:
            return None, None

        return emojis, normalize_word(match.group(1))

    # ───────── PRINT BOARD ─────────
    def print_board(self, text):

        print("\n🎮 WORDSEEK BOARD\n")

        for line in text.splitlines():

            emojis = re.findall(r"[🟩🟨🟥]", line)

            if emojis:

                word_match = re.search(r"([A-Za-z]{5})$", self.normalize_font(line))

                if word_match:

                    word = word_match.group(1)

                    print(" ".join(emojis), word)

        print()

    # ───────── SCHEDULE NEW GAME ─────────
    async def schedule_new(self, chat_id, delay=5):

        async def job():
            try:
                await asyncio.sleep(delay)

                st = self.game_state.get(chat_id)

                if not st or not st["active"]:
                    return

                if st.get("last_guess_time"):

                    self.logger.info("⏰ No reply in 2s → /new")

                    await self.app.send_message(chat_id, "/new@WordSeekBot")

            except asyncio.CancelledError:
                pass

        st = self.game_state.get(chat_id)

        if st and st.get("new_task"):
            st["new_task"].cancel()

        st["new_task"] = asyncio.create_task(job())

    # ───────── CANCEL NEW ─────────
    async def cancel_new(self, chat_id):

        st = self.game_state.get(chat_id)

        if st and st.get("new_task"):
            st["new_task"].cancel()
            st["new_task"] = None

    # ───────── SEND GUESS ─────────
    async def send_guess(self, chat_id, word):

        await asyncio.sleep(random_delay(self.speed))

        self.logger.info(f"🤔 Guess → {word.upper()}")

        st = self.game_state[chat_id]

        st["last_guess"] = word
        st["last_guess_time"] = datetime.now()

        await self.app.send_message(chat_id, word.upper())

        await self.schedule_new(chat_id)

    # ───────── HANDLERS ─────────
    def _register_handlers(self):

        app = self.app

        # START
        @app.on_message(filters.command("game") & filters.group)
        async def start_game(client, message):

            if not message.from_user or message.from_user.id != self.owner_id:
                return

            chat_id = message.chat.id

            self.game_state[chat_id] = {
                "possible_words": set(self.ALL_WORDS),
                "used_words": set(),
                "last_guess": None,
                "last_guess_time": None,
                "active": True,
                "new_task": None
            }

            await client.send_message(chat_id, "🤖 Solver Activated")

        # STOP
        @app.on_message(filters.command("sleep") & filters.group)
        async def stop_game(client, message):

            if not message.from_user or message.from_user.id != self.owner_id:
                return

            self.game_state.pop(message.chat.id, None)

            await client.send_message(message.chat.id, "😴 Solver Disabled")

        # BOT HANDLER
        @app.on_message(filters.group & filters.text)
        async def handle_bot(client, message):

            if not message.from_user:
                return

            if message.from_user.username != self.WORDSEEK_USERNAME:
                return

            chat_id = message.chat.id
            text = message.text or ""

            st = self.game_state.get(chat_id)

            if not st:
                return

            await self.cancel_new(chat_id)

            text_lower = text.lower()

            if "5-letter mode" in text_lower:
                self.print_board(text)

            if "already guessed your word" in text_lower:

                nxt = self.get_next_word(chat_id)

                if nxt:
                    await self.send_guess(chat_id, nxt)

                return

            if "game ended" in text_lower:

                await client.send_message(chat_id, "/new@WordSeekBot")
                return

            if "correct word" in text_lower:

                await asyncio.sleep(1)

                await client.send_message(chat_id, "/new@WordSeekBot")
                return

            if "game started" in text_lower:

                st["possible_words"] = set(self.ALL_WORDS)
                st["used_words"].clear()

                nxt = self.get_next_word(chat_id)

                if nxt:
                    await self.send_guess(chat_id, nxt)

                return

            if "already a game in progress" in text_lower:

                await client.send_message(chat_id, "/end@WordSeekBot")

                await asyncio.sleep(2)

                await client.send_message(chat_id, "/new@WordSeekBot")

                return

            for line in reversed(text.splitlines()):

                emojis, guess = self.parse_feedback_line(line)

                if emojis:

                    last_guess = st.get("last_guess")

                    if not last_guess:
                        return

                    st["possible_words"] = self.filter_words(
                        st["possible_words"],
                        last_guess,
                        emojis
                    )

                    nxt = self.get_next_word(chat_id)

                    if nxt:
                        await self.send_guess(chat_id, nxt)
                    else:
                        await client.send_message(chat_id, "/new@WordSeekBot")

                    return

    def run(self):

        print("🚀 WordSolver Running")

        self.app.run()
