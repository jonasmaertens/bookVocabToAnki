from genanki import Model
from pydantic import BaseModel
from typing import List, Dict, Optional

default_de_en_model = Model(
    1281009654,
    'Default (de->en)',
    fields=[
        {'name': 'German'},
        {'name': 'English'},
        {'name': 'Phonetic'},
        {'name': 'Definitions'}
    ],
    templates=[
        {
            'name': 'DE->EN',
            'qfmt': '{{German}}',
            'afmt': '{{FrontSide}}<hr id="answer"><b>{{English}}</b><br>{{Phonetic}}<br>{{Definitions}}'
        }
    ],
    css="""
    .card {
        font-family: arial;
        font-size: 20px;
        text-align: center;
        color: black;
        background-color: white;
    }
    
    .namespace_div {
        border: .5px solid white;
        margin: 10px;
        margin-top: 0;
    }
    
    #answer {
        font-size: 14px;
    }
    """
)

default_en_de_model = Model(
    1934047112,
    'Default (en->de)',
    fields=[
        {'name': 'English'},
        {'name': 'Phonetic'},
        {'name': 'Definitions'},
    ],
    templates=[
        {
            'name': 'EN->DE',
            'qfmt': '{{English}}<br>{{Phonetic}}',
            'afmt': '{{FrontSide}}<hr id="answer"><br>{{Definitions}}'
        }
    ],
    css="""
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}

.namespace_div {
    border: .5px solid white;
    margin: 10px;
    margin-top: 0;
}

#answer {
    font-size: 14px;
}
"""
)


class Reference(BaseModel):
    id: str
    name: str


class Definition(BaseModel):
    property: Optional[str] = None
    references: Optional[List[Reference]] = None
    description: str
    examples: Optional[List[str]] = []
    extra_example: Optional[List[str]] = []
    synonyms: Optional[Dict[str, List[str]]] = {}
    german_translation: str


class DefinitionStack(BaseModel):
    namespace: str
    definitions: List[Definition]


class WordFormDefinitionStack(BaseModel):
    id: str
    word_form: str
    definitions: List[DefinitionStack]


class WordData(BaseModel):
    ipa: str
    definitions: List[WordFormDefinitionStack]


def map_word_data_to_anki(word: str, word_data: WordData):
    """
    Maps a word and its data to anki fields for both the english to german and german to english models
    :param word: the word
    :param word_data: the data for the word
    :return: (en_to_de_values, de_to_en_values)
    """
    ipa = word_data.ipa
    definitions = _build_definition_string(word_data)
    en_to_de_values = (word, ipa, definitions)
    # filter definitions by german translation
    defs_by_de = {}
    for word_form_stack in word_data.definitions:
        for def_stack in word_form_stack.definitions:
            for definition in def_stack.definitions:
                if definition.german_translation not in defs_by_de:
                    defs_by_de[definition.german_translation] = []
                defs_by_de[definition.german_translation].append((definition, def_stack.namespace))
    de = "<br>".join(defs_by_de.keys())
    word_data_de = WordData(ipa=ipa, definitions=[WordFormDefinitionStack(id="", word_form="", definitions=[])])
    for german_translation, definitions in defs_by_de.items():
        word_data_de.definitions[0].definitions.append(
            DefinitionStack(namespace=german_translation if len(definitions) > 1 else "__GLOBAL__",
                            definitions=[Definition.model_validate(definition[0]) for
                                         definition in definitions]))
    de_to_en_values = (de, word, ipa, _build_definition_string(word_data_de, False))
    return en_to_de_values, de_to_en_values


def _build_definition_string(word_data, include_german_translation=True):
    definitions = ""
    for word_form_stack in word_data.definitions:
        for def_stack in word_form_stack.definitions:
            if def_stack.namespace == "__GLOBAL__":
                namespace = ""
            else:
                namespace = f"<br><br>{def_stack.namespace}<br>"
            definitions += namespace
            for definition in def_stack.definitions:
                definitions += "<hr class='namespace_div'>"
                definitions += f"<i>{word_form_stack.word_form}</i><br>" if word_form_stack.word_form else ""
                if include_german_translation:
                    definitions += f"<br>Übersetzung: <b>{definition.german_translation}</b><br><br>"
                definitions += (
                                   f"[<i>{definition.property.replace("[", "").replace("]", "")}</i>] " if definition.property else "") + (
                                   f"{definition.description}<br>")
                if definition.examples:
                    definitions += "<ul>"
                    if len(definition.examples) > 2:
                        definition.examples = definition.examples[:2]
                    for example in definition.examples:
                        definitions += f"<li>{example}</li>"
                    definitions += "</ul><br>"
                if definition.synonyms or definition.references:
                    definitions += "Synonyms/References: "
                    references_list = [ref.name for ref in definition.references] if definition.references else []
                    synonyms_list = [word for words in definition.synonyms.values() for word in
                                     words] if definition.synonyms else []
                    definitions += "▪".join(references_list + list(synonyms_list))
    return definitions
