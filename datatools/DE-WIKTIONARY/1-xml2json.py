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

print('Loading wiktionary, please wait...', end='')
sys.stdout.flush()
wiki = XMLfile_Provider('in/dewiktionary-20170201-pages-articles.xml')
print(' done!')
kwmgr = KeywordManager()
num_articles = len(wiki.articles.keys())

terms = {}
widgets=[FormatLabel('   Article: %(message)s [%(value)s/'+str(num_articles)+']'), ' ', Percentage(), ' ', Bar(marker='#', left='[', right=']'), ' ', ETA()]
pBar = ProgressBar(widgets=widgets, maxval=num_articles).start()
outfile = codecs.open('in/de-wiktionary.json', 'w', 'utf-8')
print('[', file=outfile)

for i, title in enumerate(wiki.articles.keys()):
    pBar.update(i, title)
    page = ArticleParser(title, wiki.articles[title], kwmgr)
    page.parse()
    sections = json.dumps(page.sections, indent=4)
    if i>0:
        print(',', file=outfile)
    print(sections, file=outfile, end='')

print('\n]', file=outfile)
outfile.close()
kwmgr.dump_keywords('in/keywords.txt')
kwmgr.save_keywords('in/keywords.json')

