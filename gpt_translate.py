import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def translate_en_to_de_with_definition(word, context, definition):
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": """You are a translator that helps translate english words to german based on the context. 
            Your input will consist of a tuple of the english word, an optional context, and a definition. 
            Your output will just consist of german words that you think best represent the english word in the given context, separated by a comma.
            Example 1:
                Input: ("game", "fun", "an activity that you do to have fun, often one that has rules and that you can win or lose; the equipment for a game")
                Output: "Spiel"
            Example 2:
                Input: ("game", wild animals/birds", "wild animals or birds that people hunt for sport or food")
                Output: "Wild, Jagdfauna"
            Example 3:
                Input: ("curmudgeon", "", "a person who gets annoyed easily, often an old person")
                Output: "Miesepeter, Muffel, Griesgram"
            """},
            {
                "role": "user",
                "content": f"(\"{word}\", \"{context}\", \"{definition}\")"
            }
        ]
    )

    return completion.choices[0].message.content.replace('"', '')

