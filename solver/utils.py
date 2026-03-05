import random
import unicodedata
import re


def normalize_word(word: str) -> str:
    text = unicodedata.normalize("NFKD", word)
    return "".join(c for c in text if c.isalpha()).lower()


def normalize_text(text: str) -> str:
    return re.sub(r"[^a-z\s]", "", text.lower())


def random_delay(speed: float):
    return random.uniform(max(0.5, speed - 0.3), speed)
