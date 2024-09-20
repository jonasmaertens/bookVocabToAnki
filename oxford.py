#!/bin/env python3

""" oxford dictionary api """
from http import cookiejar

import requests
from bs4 import BeautifulSoup as soup


class WordNotFound(Exception):
    """ word not found in dictionary (404 status code) """
    pass


class BlockAll(cookiejar.CookiePolicy):
    """ policy to block cookies """
    return_ok = set_ok = domain_return_ok = path_return_ok = lambda self, *args, **kwargs: False
    netscape = True
    rfc2965 = hide_cookie2 = False


class Word:
    """ retrieve word info from oxford dictionary website """
    entry_selector = '#entryContent > .entry'
    header_selector = '.top-container'

    title_selector = header_selector + ' .headword'
    wordform_selector = header_selector + ' .pos'
    property_global_selector = header_selector + ' .grammar'

    br_pronounce_selector = '[geo=br] .phon'
    am_pronounce_selector = '[geo=n_am] .phon'
    br_pronounce_audio_selector = '[geo=br] [data-src-ogg]'
    am_pronounce_audio_selector = '[geo=n_am] [data-src-ogg]'

    definition_body_selector = '.senses_multiple'
    definition_body_single_selector = '.sense_single'
    definition_phrasal_verbs_selector = '.phrasal_verb_links'
    namespaces_selector = '.senses_multiple > .shcut-g'
    examples_selector = '.senses_multiple .sense > .examples .x'
    extra_examples_selector = '[unbox=extra_examples] .examples .unx'
    definitions_selector = '.senses_multiple .sense > .def'
    synonyms_main_selector = '[unbox=synonyms] .body > span:first-child'
    synonyms_body_selector = '[unbox=synonyms] .body > span:has(.bulletsep)'

    phrasal_verbs_selector = '.phrasal_verb_links a'
    idioms_selector = '.idioms > .idm-g'
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'

    other_results_selector = '#rightcolumn #relatedentries'

    def __init__(self, word, by_id=False):
        # URL-encode the word
        self.word = requests.utils.quote(word)
        self.soup_data = None
        self._fetch_data(by_id)

    def _fetch_data(self, by_id=False):
        req = requests.Session()
        req.cookies.set_policy(BlockAll())

        page_html = req.get(self.get_url(by_id), timeout=5, headers={'User-agent': self.user_agent})
        if page_html.status_code == 404:
            raise WordNotFound
        else:
            self.soup_data = soup(page_html.content, 'html.parser')

        if self.soup_data is not None:
            self._clean_soup()

    def _clean_soup(self):
        self.delete('[title="Oxford Collocations Dictionary"]')
        self.delete('[title="British/American"]')  # edge case: 'phone'
        self.delete('[title="Express Yourself"]')
        self.delete('[title="Collocations"]')
        self.delete('[title="Word Origin"]')

    def get_url(self, by_id):
        baseurl = 'https://www.oxfordlearnersdictionaries.com/search/english/direct/?q=' \
            if not by_id else 'https://www.oxfordlearnersdictionaries.com/definition/english/'
        return baseurl + self.word

    def delete(self, selector):
        try:
            for tag in self.soup_data.select(selector):
                tag.decompose()
        except IndexError:
            pass

    @property
    def name(self):
        if self.soup_data is None:
            return None
        return self.soup_data.select(self.title_selector)[0].text

    @property
    def id(self):
        if self.soup_data is None:
            return None
        return self.soup_data.select(self.entry_selector)[0].attrs['id']

    @property
    def wordform(self):
        if self.soup_data is None:
            return None
        try:
            return self.soup_data.select(self.wordform_selector)[0].text
        except IndexError:
            return None

    @property
    def property_global(self):
        if self.soup_data is None:
            return None
        try:
            return self.soup_data.select(self.property_global_selector)[0].text
        except IndexError:
            return None

    def get_prefix_from_filename(self, filename):
        if '_gb_' in filename:
            return 'BrE'
        elif '_us_' in filename:
            return 'NAmE'
        return None

    @property
    def pronunciations(self):
        if self.soup_data is None:
            return None

        britain = {'prefix': None, 'ipa': None, 'url': None}
        america = {'prefix': None, 'ipa': None, 'url': None}

        try:
            britain_pron_tag = self.soup_data.select(self.br_pronounce_selector)[0]
            america_pron_tag = self.soup_data.select(self.am_pronounce_selector)[0]

            britain['ipa'] = britain_pron_tag.text
            britain['prefix'] = 'BrE'
            america['ipa'] = america_pron_tag.text
            america['prefix'] = 'nAmE'
        except IndexError:
            pass

        try:
            britain['url'] = self.soup_data.select(self.br_pronounce_audio_selector)[0].attrs['data-src-ogg']
            america['url'] = self.soup_data.select(self.am_pronounce_audio_selector)[0].attrs['data-src-ogg']
        except IndexError:
            pass

        if britain['prefix'] is None and britain['url'] is not None:
            britain['prefix'] = self.get_prefix_from_filename(britain['url'])

        if america['prefix'] is None and america['url'] is not None:
            america['prefix'] = self.get_prefix_from_filename(america['url'])

        return [britain, america]

    @property
    def other_results(self):
        if self.soup_data is None:
            return None

        info = []

        try:
            rightcolumn_tags = self.soup_data.select(self.other_results_selector)[0]
        except IndexError:
            return None

        header_tags = rightcolumn_tags.select('dt')
        other_results_tags = rightcolumn_tags.select('dd')

        for header_tag, other_results_tag in zip(header_tags, other_results_tags):
            header = header_tag.text
            other_results = []

            for item_tag in other_results_tag.select('li'):
                names = item_tag.select('span')[0].find_all(text=True, recursive=False)
                wordform_tag = item_tag.select('pos')
                names.append(wordform_tag[0].text if len(wordform_tag) > 0 else '')
                other_results.append(names)

            other_results = list(filter(None, other_results))
            ids = [self.extract_id(tag.attrs['href']) for tag in other_results_tag.select('li a')]

            results = []
            for other_result, id in zip(other_results, ids):
                result = {}
                result['name'] = ' '.join(list(map(lambda x: x.strip(), other_result[0:-1])))
                result['id'] = id

                try:
                    result['wordform'] = other_result[-1].strip()
                except IndexError:
                    pass

                results.append(result)

            info.append({header: results})

        return info

    def extract_id(self, link):
        return link.split('/')[-1]

    def get_references(self, tags):
        if self.soup_data is None:
            return None

        references = []
        for tag in tags.select('.xrefs a'):
            id = self.extract_id(tag.attrs['href'])
            word = tag.text
            references.append({'id': id, 'name': word})

        return references

    @property
    def references(self):
        if self.soup_data is None:
            return None

        header_tag = self.soup_data.select(self.header_selector)[0]
        return self.get_references(header_tag)

    @property
    def definitions(self):
        if self.soup_data is None:
            return None
        return [tag.text for tag in self.soup_data.select(self.definitions_selector)]

    @property
    def examples(self):
        if self.soup_data is None:
            return None
        return [tag.text for tag in self.soup_data.select(self.examples_selector)]

    @property
    def phrasal_verbs(self):
        if self.soup_data is None:
            return None

        phrasal_verbs = []
        for tag in self.soup_data.select(self.phrasal_verbs_selector):
            phrasal_verb = tag.select('.xh')[0].text
            id = self.extract_id(tag.attrs['href'])

            phrasal_verbs.append({'name': phrasal_verb, 'id': id})

        return phrasal_verbs

    def _parse_definition(self, parent_tag):
        if self.soup_data is None:
            return None

        definition = {}

        try:
            definition['property'] = parent_tag.select('.grammar')[0].text
        except IndexError:
            pass

        try:
            definition['label'] = parent_tag.select('.labels')[0].text
        except IndexError:
            pass

        try:
            definition['refer'] = parent_tag.select('.dis-g')[0].text
        except IndexError:
            pass

        definition['references'] = self.get_references(parent_tag)
        if not definition['references']:
            definition.pop('references', None)

        try:
            definition['description'] = parent_tag.select('.def')[0].text
        except IndexError:
            pass

        definition['examples'] = [example_tag.text for example_tag in parent_tag.select('.examples .x')]

        definition['extra_example'] = [
            example_tag.text for example_tag in parent_tag.select(self.extra_examples_selector)
        ]

        synonyms_main = parent_tag.select(self.synonyms_main_selector)
        if synonyms_main:
            definition['synonyms'] = {synonyms_main[0].text: [
                word for word in parent_tag.select(self.synonyms_body_selector)[0].text.split(' ▪ ')
            ]}
        else:
            definition['synonyms'] = {}

        return definition

    @property
    def definition_full(self):
        if self.soup_data is None:
            return None

        namespace_tags = self.soup_data.select(self.namespaces_selector)

        info = []
        for namespace_tag in namespace_tags:
            try:
                namespace = namespace_tag.select('h2.shcut')[0].text
            except IndexError:
                namespace = None

            definitions = []
            definition_full_tags = namespace_tag.select('.sense')

            for definition_full_tag in definition_full_tags:
                definition = self._parse_definition(definition_full_tag)
                definitions.append(definition)

            info.append({'namespace': namespace, 'definitions': definitions})

        if len(info) == 0:
            info.append({'namespace': '__GLOBAL__', 'definitions': []})
            def_body_tags = self.soup_data.select(self.definition_body_selector)
            if len(def_body_tags) == 0:
                def_body_tags = self.soup_data.select(self.definition_body_single_selector)
            if len(def_body_tags) == 0:
                info[0]['definitions'] = [{
                    'description': f"As phrasal verb(s) {" and ".join([f"'{pv['name']}'" for pv in self.phrasal_verbs])}",
                }]
                return info

            definitions = []
            definition_full_tags = def_body_tags[0].select('.sense')

            for definition_full_tag in definition_full_tags:
                definition = self._parse_definition(definition_full_tag)
                definitions.append(definition)

            info[0]['definitions'] = definitions

        return info

    @property
    def idioms(self):
        idiom_tags = self.soup_data.select(self.idioms_selector)

        idioms = []
        for idiom_tag in idiom_tags:
            try:
                idiom = idiom_tag.select('.idm-l')[0].text
            except IndexError:
                idiom = idiom_tag.select('.idm')[0].text

            global_definition = {}

            try:
                global_definition['label'] = idiom_tag.select('.labels')[0].text
            except IndexError:
                pass

            try:
                global_definition['refer'] = idiom_tag.select('.dis-g')[0].text
            except IndexError:
                pass

            global_definition['references'] = self.get_references(idiom_tag)
            if not global_definition['references']:
                global_definition.pop('references', None)

            definitions = []
            for definition_tag in idiom_tag.select('.sense'):
                definition = {}

                try:
                    definition['description'] = definition_tag.select('.def')[0].text
                except IndexError:
                    pass

                try:
                    definition['label'] = definition_tag.select('.labels')[0].text
                except IndexError:
                    pass

                try:
                    definition['refer'] = definition_tag.select('.dis-g')[0].text
                except IndexError:
                    pass

                definition['references'] = self.get_references(definition_tag)
                if not definition['references']:
                    definition.pop('references', None)

                definition['examples'] = [example_tag.text for example_tag in definition_tag.select('.x')]
                definitions.append(definition)

            idioms.append({'name': idiom, 'summary': global_definition, 'definitions': definitions})

        return idioms

    @property
    def info(self):
        if self.soup_data is None:
            return None

        word = {
            'id': self.id,
            'name': self.name,
            'wordform': self.wordform,
            'pronunciations': self.pronunciations,
            'property': self.property_global,
            'definitions': self.definition_full,
            'idioms': self.idioms,
            'other_results': self.other_results
        }

        if not word['property']:
            word.pop('property', None)

        if not word['other_results']:
            word.pop('other_results', None)

        if word['wordform'] == 'verb':
            word['phrasal_verbs'] = self.phrasal_verbs

        return word

    def __repr__(self):
        return f"Word({self.word}, properties={self.info})"
