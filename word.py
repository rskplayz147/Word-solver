import json
import importlib.resources as pkg_resources


def load_words():
    with pkg_resources.open_text("solver", "allWords.json") as f:
        all_words = {
            w.lower()
            for w in json.load(f)
            if isinstance(w, str) and len(w) == 5 and w.isalpha()
        }

    with pkg_resources.open_text("solver", "commonWords.json") as f:
        common_words = json.load(f)

    return all_words, common_words