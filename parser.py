from bs4 import BeautifulSoup
import re
from glob import glob
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class NotesParser:
    MAX_WORD_LENGTH = 25
    @classmethod
    def parse_kindle_html_vocab(cls, file_path):
        with open(file_path, 'r', encoding="utf8") as f:
            html = f.read()
        bs = BeautifulSoup(html, features="html.parser")
        markings =  [cls._clean(div.getText()) for div in bs.find_all(name="div", attrs={"class": "noteText"})]
        return [word for word in markings if len(word) < cls.MAX_WORD_LENGTH]

    @classmethod
    def parse_apple_books_vocab(cls, file_path):
        with open(file_path, 'r', encoding="utf8") as f:
            lines = f.readlines()
        words = []
        i = 0
        while i < len(lines):
            pattern = r"\d*\.\s[a-zA-Z]*\s\d{4}\s{2}"
            if re.match(pattern, lines[i]):
                word = cls._clean(lines[i + 1])
                if len(word) < cls.MAX_WORD_LENGTH:
                    words.append(word)
                    i += 1
            i += 1
        return words

    @classmethod
    def parse_any(cls, file_path):
        with open(file_path, "r", encoding="utf8") as f:
            content = f.read()
        if "<html" in content and "noteText" in content:
            logger.info(f"Parsing {file_path} as Kindle HTML export")
            return cls.parse_kindle_html_vocab(file_path)
        elif "\nNOTES FROM\n" in content:
            logger.info(f"Parsing {file_path} as Apple Books export")
            return cls.parse_apple_books_vocab(file_path)
        else:
            raise NotImplementedError("This export type is not supported yet.")

    @classmethod
    def parse_all_in_dir(cls, dir_path):
        vocab = []
        for file in glob(f"{dir_path}/*"):
            try:
                vocab += cls.parse_any(file)
            except NotImplementedError:
                logger.warning(f"Skipping file {file} as the type is not supported")
        return vocab

    @classmethod
    def _clean(cls, word:str):
        return re.sub(r"[^a-zØ-öø-ÿ]", "", word.strip().lower())

