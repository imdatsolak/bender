# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import codecs
import json
import re

from modules.ArticleParser import ArticleParser, KeywordManager
from modules.Provider import XMLfile_Provider
from progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker

gm_re = re.compile(r'^[^\[]+\[\[([^\]]+)\]\].*')
de_re = re.compile(r'[^=]+=')
samples_re = re.compile(r'^:\[[^]]+] ')
others_re = re.compile(r'{{[^}]+}}')
lang_spec = re.compile(r'\[\[..:([^]]+)].*')
html = re.compile(r'<[^>]+>')
def clean_article(page):
    page_sections = page

    title = page_sections['title']
    base_form = None
    parent_terms = []
    grammer_base = None
    hyphenation = None
    word_type = None
    declinations = []
    synonyms = []
    examples = []
    similars = []
    is_toponym = False
    see_also = None
    sa = page_sections.get('see_also', None)
    if sa != None:
        see_also = sa.get('main', None)


    if 'Oberbegriffe' in page_sections:
        gm = page_sections['Oberbegriffe']
        if 'main' in gm:
            gm = gm['main']
        for entry in gm:
            entry = samples_re.sub('', entry)
            entry = gm_re.sub(r'\1', entry)
            entry = entry.replace('[[', '')
            entry = entry.replace(']]', '')
            if entry not in parent_terms:
                parent_terms.append(entry)

    if 'Grammatische Merkmale' in page_sections:
        gm = page_sections['Grammatische Merkmale']
        if 'main' in gm:
            gm = gm['main']
        if len(gm) > 0:
            entry = gm[0]
        else:
            entry = gm
        if len(entry):
            entry = gm_re.sub(r'\1', entry)
            grammer_base = entry


    is_verb = True
    base_form = page_sections.get('Grundformverweis Konj', None)
    if base_form == None:
        base_form = page_sections.get('Grundformverweis Dekl', None)
        is_verb = False
    if base_form != None:
        if 'main' in base_form:
            base_form = base_form['main']
        if 'attributes' in base_form[0]:
            base_form = base_form[0]['attributes']
        for entry in base_form:
            if '=' not in entry:
                if gm_re.match(entry):
                    base_form = gm_re.sub(r'\1', entry)
                else:
                    base_form = entry
                break


    german = page_sections.get('Deutsch')
    if german != None:
        wordDekl = german[german.keys()[0]]
        for entry in wordDekl:
            if 'Genus' in entry:
                continue
            elif 'Nominativ' in entry or 'Genitiv' in entry or 'Dativ' in entry or 'Akkusativ' in entry:
                entry = de_re.sub('', entry)
                if entry not in declinations:
                    if entry != u'\u2014':
                        declinations.append(entry)
        if german.keys()[0] == 'Toponym':
            is_toponym = True


    if 'Synonyme' in page_sections:
        gm = page_sections['Synonyme']
        if 'main' in gm:
            gm = gm['main']
        if len(gm):
            entry = gm[0]
            if ', ' in entry:
                entries = entry.split(',')
                for a in entries:
                    a = a.strip()
                    a = samples_re.sub('', a)
                    a = a.replace('[[', '')
                    a = a.replace(']]', '')
                    if a not in synonyms:
                        synonyms.append(a)
            else:
                entry = gm_re.sub(r'\1', entry)
                if entry not in synonyms:
                    synonyms.append(entry)


    if 'Beispiele' in page_sections:
        gm = page_sections['Beispiele']
        if 'main' in gm:
            gm = gm['main']
        for entry in gm:
            entry = samples_re.sub('', entry)
            entry = others_re.sub('', entry)
            entry = entry.replace("''", "")
            if entry.startswith(':: '):
                entry = entry.replace(':: ', '')
            entry = entry.replace('::', '')
            entry = html.sub('', entry)
            entry = entry.replace(u'\u201c', '')
            entry = entry.replace(u'\u201e', '')
            if entry not in examples:
                examples.append(entry)


    if u"\u00c4hnlichkeiten" in page_sections:
        gm = page_sections[u"\u00c4hnlichkeiten"]
        if 'main' in gm:
            gm = gm['main']
        if len(gm) > 1 and 'attributes' in gm[0]:
            gm = gm[0]['attributes']
        for entry in gm:
            try:
                if len(entry) > 0 and 'attributes' in entry:
                    entry = entry['attributes']
                if gm_re.match(entry):
                    entry = gm_re.sub(r'\1', entry)
                    if ', ' in entry:
                        entries = entry.split(',')
                        for a in entries:
                            a = a.strip()
                            a = samples_re.sub('', a)
                            a = lang_spec.sub(r'\1', a)
                            a = a.replace('[[', '')
                            a = a.replace(']]', '')
                            if a not in similars:
                                similars.append(a)
                    else:
                        entry = others_re.sub('', entry)
                        entry = lang_spec.sub(r'\1', entry)
                        entry = entry.replace('[[', '')
                        entry = entry.replace(']]', '')
                        if entry not in similars:
                            similars.append(entry)
            except:
                pass
                # print('*** Offending entry = [%s]' % entry)
                # print('*** SECTION: ', page_sections)


    data = { title : {
                'base_form' : base_form,
                'grammer_base': grammer_base,
                'is_verb': is_verb,
                'declinations': declinations,
                'examples': examples,
                'synonyms': synonyms,
                'similars': similars,
                'is_toponym': is_toponym,
                'parents': parent_terms
                }
            }
    return data



print('Loading de-wiktionary.json...', end='')
sys.stdout.flush()
pages = json.load(codecs.open('in/de-wiktionary.json', 'r', 'utf-8'))
print(' done')
print('Parsing...', end='')
sys.stdout.flush()
result = {}
num_articles = len(pages)
widgets=[FormatLabel('   Article: %(message)s [%(value)s/'+str(num_articles)+']'), ' ', Percentage(), ' ', Bar(marker='#', left='[', right=']'), ' ', ETA()]
pBar = ProgressBar(widgets=widgets, maxval=num_articles).start()

for i,page in enumerate(pages):
    pBar.update(i, page['title'])
    result.update(clean_article(page))

pBar.finish()
json.dump(result, codecs.open('out/de-wiktionary-db.json', 'w', 'utf-8'), indent=4)
