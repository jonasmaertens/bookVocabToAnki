# Anki Vocabulary Deck Generator

This project generates Anki decks from vocabulary words extracted from Kindle and Apple Books exports. It uses a modified version of [Oxford Dictionary API](https://github.com/NearHuscarl/oxford-dictionary-api) to web-scrape the Oxford Dictionary for word definitions and the OpenAI API to translate definitions into German. An Anki deck is then generated (both de->en and en->de) with the parsed and translated vocabulary using the [genAnki](https://github.com/kerrickstaley/genanki) library and custom note templates.

## Features

- Parse vocabulary words from Kindle and Apple Books exports.
- Fetch word definitions from the Oxford Dictionary.
- Translate definitions into German using OpenAI's GPT-4o model.
- Generate Anki decks with the parsed and translated vocabulary.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/jonasmaertens/anki-vocab-deck-generator.git
    cd anki-vocab-deck-generator
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Set up your environment variables:
    - `OPENAI_API_KEY`: Your OpenAI API key.

## Usage

1. Place your Kindle or Apple Books export files in the `raw_sources` directory.

2. Run the script to generate the Anki deck:
    ```sh
    python anki_generator.py
    ```

3. The generated Anki deck will be saved as `anki_deck.apkg`.

## Project Structure

- `anki_generator.py`: Main script to generate Anki decks.
- `oxford.py`: Module to interact with the Oxford Dictionary API.
- `gpt_translate.py`: Module to translate definitions using OpenAI's GPT-4o model.
- `parser.py`: Module to parse Kindle and Apple Books exports.
- `anki_models.py`: Module defining Anki note models and mapping functions.

## License

This project is licensed under the MIT License.