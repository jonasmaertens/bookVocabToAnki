import time
import os
import json
from random import shuffle

from genanki import Note, Deck
from anki_models import default_de_en_model, default_en_de_model, map_word_data_to_anki, WordData
from oxford import Word, WordNotFound
from gpt_translate import translate_en_to_de_with_definition
from parser import NotesParser
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class AnkiDeckGenerator:
    def __init__(self):
        # create or load data json
        if os.path.exists("data/data.json"):
            with open("data/data.json", "r", encoding="utf8") as file:
                self.data = json.load(file)
        else:
            self.data = {}
            os.makedirs("data", exist_ok=True)
            with open("data/data.json", "w") as file:
                json.dump(self.data, file)

    @staticmethod
    def scrape_dictionary(word: str = None, word_id: str = None):
        if (word is None and word_id is None) or (word is not None and word_id is not None):
            raise ValueError("Exactly one of word or word_id must be provided.")
        word_info = Word(word) if word else Word(word_id, by_id=True)
        ipa = None
        if word_info.pronunciations:
            for pron in word_info.pronunciations:
                if pron["prefix"] == "nAmE":
                    ipa = pron["ipa"]
                    break
            else:
                ipa = word_info.pronunciations[0]["ipa"]
        definitions = word_info.definition_full
        return {"ipa": ipa, "definitions": definitions, "word": word_info.name, "id": word_info.id,
                "word_form": word_info.wordform}

    def get_data_for_word_list(self, word_list):
        logger.info(f"Processing {len(word_list)} words...")
        for word in word_list:
            logger.info(f"Processing {word}...")
            if word in self.data:
                logger.info(f"Word {word} already in data.")
                continue
            time.sleep(1)
            word_info = AnkiDeckGenerator.scrape_dictionary(word=word)
            base_word = word_info["word"]
            if base_word in self.data:
                logger.info(f"Word {base_word} already in data.")
                continue
            word_data = {"ipa": word_info["ipa"]}
            self.populate_definitions(word_info)
            word_data["definitions"] = [{
                "id": word_info["id"],
                "word_form": word_info["word_form"],
                "definitions": word_info["definitions"]}]
            if "_1" in word_info["id"]:
                i = 2
                word_info = AnkiDeckGenerator.scrape_dictionary(word_id=word_info["id"].replace("_1", f"_{i}"))
                while word_info is not None and "_" in word_info["id"]:
                    self.populate_definitions(word_info)
                    word_data["definitions"].append({
                        "id": word_info["id"],
                        "word_form": word_info["word_form"],
                        "definitions": word_info["definitions"]
                    })
                    try:
                        word_info = AnkiDeckGenerator.scrape_dictionary(
                            word_id=word_info["id"].replace(f"_{i}", f"_{i + 1}"))
                        i += 1
                    except WordNotFound:
                        word_info = None
            self.data[base_word] = word_data
            with open("data/data.json", "w", encoding="utf8") as file:
                json.dump(self.data, file, ensure_ascii=False)

    @staticmethod
    def populate_definitions(word_info):
        for def_stack in word_info["definitions"]:
            logger.info(f"\tTranslating {word_info["word"]} ({def_stack["namespace"]})...")
            for definition in def_stack["definitions"]:
                description = definition["description"]
                logger.info(f"\t\tDefinition: {description}")
                namespace = def_stack["namespace"] if def_stack["namespace"] != "__GLOBAL__" else ""
                german_translation = translate_en_to_de_with_definition(word_info["word"], namespace, description)
                logger.info(f"\t\tTranslation: {german_translation}")
                definition["german_translation"] = german_translation

    def generate_anki_deck(self):
        deck = Deck(1318074875, "Books Vocabulary")
        for word, word_data in self.data.items():
            en_to_de, de_to_en = map_word_data_to_anki(word, WordData.model_validate(word_data))
            note = Note(
                model=default_en_de_model,
                fields=en_to_de
            )
            deck.add_note(note)
            note = Note(
                model=default_de_en_model,
                fields=de_to_en
            )
            deck.add_note(note)
        shuffle(deck.notes)
        deck.write_to_file("anki_deck.apkg")


if __name__ == "__main__":
    vocab = NotesParser.parse_all_in_dir("raw_sources")
    vocab = list(set(vocab))
    generator = AnkiDeckGenerator()
    generator.get_data_for_word_list(vocab)
    generator.generate_anki_deck()
