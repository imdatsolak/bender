# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# Copyright (c) 2004 Guaka
# Copyright (c) 2019 Imdat Solak
#
# ArticleParser
# Written: 2017-??-?? ??:?? CET, ISO
#          - Based on wik2dict's ArticleParser
#         
# wik2dict is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""
Provider classes.

Modified: 2017-02-17, ISO
"""
#
import os
import re
import bz2, gzip
from sets import Set

import pprint
import re
import codecs
import json

see_also = re.compile(r'^\{\{Siehe auch\|([^\}]+)\}\}')
title = re.compile(r'^== ([^=]+)==$')
special_heading = re.compile(r'^=== (\{\{[^=]+)===$')
sub_heading = re.compile(r'^==== ([^=]+)====$')
multi_line_section = re.compile(r'^\{\{(.*)$')
section = re.compile(r'^\{\{([^\}]+)\}\}')
class KeywordManager:
    def __init__(self, filename=None):
        self.keywords = {}
        if filename is not None:
            self.load_keywords(filename)

    def get_clean_kw(self, kw):
        return self.keywords.get(kw, None)

    def add_dirty_kw(self, kw):
        if kw is not None and kw not in self.keywords.keys():
            self.keywords[kw] = kw

    def dump_keywords(self, outfile_name):
        f = codecs.open(outfile_name, 'w', 'utf-8')
        for kw in self.keywords.keys():
            print('%s|%s' % (kw, self.keywords[kw]), file=f)
        f.close()

    def save_keywords(self, filename):
        json.dump(self.keywords, codecs.open(filename, 'w', 'utf-8'))

    def load_keywords(self, filename):
        self.keywords = json.load(codecs.open(filename, 'r', 'utf-8'))



class ArticleParser:
    def __init__(self, title, article_text, keyword_mgr = None):
        self.article_text = article_text
        self.sections = {'title': title}
        self.article_title = title
        self.current_section = None
        self.sub_section = None
        self.keyword_mgr = keyword_mgr

    def _append_to_title(self, title_data):
        return None

    def _set_see_also(self, tag):
        tag = tag.replace('[', '')
        tag = tag.replace(']', '')
        self.sections['see_also'] = {'main': tag}
        self.sub_section = None
        self.keyword_mgr.add_dirty_kw('see_also')

    def _set_special_heading(self, heading_data):
        """
        Handles:
            === {{Wortart|Substantiv|Deutsch}}, {{m}} ===
            === {{Wortart|Substantiv|Deutsch}}, {{mf}}, {{Wortart|Nachname|Deutsch}} ===
        We should receive:
            {{Wortart|Substantiv|Deutsch}}, {{m}}
            {{Wortart|Substantiv|Deutsch}}, {{mf}}, {{Wortart|Nachname|Deutsch}}
        as 'heading_data'. 'left_heading' may contain additional information
        I hope this is the only type of this 'special heading'
        """
        heading_entries = []
        heading_keyword = None
        heading_data = heading_data.replace('{{', '#')
        heading_data = heading_data.replace('}}', '')
        if heading_data.startswith('#'):    # Otherwise python may deliver an empty entry at [0]
            heading_data = heading_data[1:]
        headings = heading_data.split('#')
        left_heading = headings[0]
        if '|' in left_heading:
            lhs_data = left_heading.split('|')
            heading_keyword = lhs_data[0]
            del lhs_data[0]
            heading_entries.extend([lh.strip() for lh in lhs_data])
        else:
            heading_keyword = left_heading
        if len(headings) > 1:
            del headings[0]
            for lh in headings:
                if '|' not in lh:
                    heading_entries.append(lh)
                else:
                    new_headings = lh.split('|')
                    heading_entries.append([nlh.strip() for nlh in new_headings])
        if len(heading_entries) > 0:
            # Sometimes, there is more than one this kind of subsection in 
            # wiktionary. This happens when a word is, e.g., a term as well as a name.
            # In such a case, we just extend the section-information
            if self.sections.get(heading_keyword, None) != None:
                self.sections[heading_keyword]['main'].extend(heading_entries)
            else:
                self.sections[heading_keyword] = {'main' : heading_entries}

        self.keyword_mgr.add_dirty_kw(heading_keyword)
        self.current_section = None
        self.sub_section = None

    def _set_subheading(self, sub_heading):
        """
        Handles:
            ==== Übersetzungen ====
        We receive only what is between the '==='
        """
        sub_heading = sub_heading.strip()
        self.current_section = sub_heading
        self.sub_section = None
        if self.sections.get(self.current_section, None) == None:
            self.sections[self.current_section] = {'main' : []}
        self.keyword_mgr.add_dirty_kw(self.current_section)


    def _set_section(self, section):
        self.sub_section = None
        section = section.strip()
        self.current_section = None
        self.sub_section = None
        if 'Ü-Tabel' in section:
            return
        section_data = section.split('|')
        self.current_section = section_data[0]
        self.keyword_mgr.add_dirty_kw(self.current_section)
        if self.sections.get(self.current_section, None) == None:
            self.sections[self.current_section] = {'main' : []}
        if len(section_data) > 1: # There are additional parameters we need to store
            del section_data[0]
            self.sections[self.current_section]['main'].append({'attributes': [att.strip() for att in section_data]})


    def _set_multiline_section(self, section):
        section = section.strip()
        self.current_section = None
        self.sub_section = None
        if 'Ü-Tabel' in section:
            return
        section_data = section.split(' ')
        self.current_section = section_data[0]
        if self.sections.get(self.current_section, None) == None:
            self.sections[self.current_section] = {'main' : []}
        if len(section_data) > 1: # There are additional parameters we need to store
            del section_data[0]
            self.sub_section = section_data[0]
            self.keyword_mgr.add_dirty_kw(self.sub_section)
            self.sections[self.current_section] = {self.sub_section : []}
        self.keyword_mgr.add_dirty_kw(self.current_section)


    def _add_to_current_section(self, line):
        line = line.strip()
        if len(line) == 0:
            return
        # Of course, we still need to do a lot of pre-processing of lines
        if self.current_section is not None:
            if self.sub_section is None:
                sub_section = 'main'
            else:
                sub_section = self.sub_section
            if self.sections.get(self.current_section, None) != None:
                if self.sections[self.current_section].get(sub_section, None) != None:
                    self.sections[self.current_section][sub_section].append(line)
                else:
                    self.sections[self.current_section] = {sub_section: [line]}
            else:
                self.sections[self.current_section] = {'main': [line]}


    def parse(self):
        lines = self.article_text.split('\n')
        for line in lines:
            if see_also.match(line) is not None:
                self._set_see_also(see_also.sub(r'\1', line))

            elif title.match(line) is not None:
                self._append_to_title(title.sub(r'\1', line))

            elif special_heading.match(line) is not None:
                self._set_special_heading(special_heading.sub(r'\1', line))

            elif sub_heading.match(line) is not None:
                self._set_subheading(sub_heading.sub(r'\1', line))

            elif section.match(line) is not None:
                self._set_section(section.sub(r'\1', line))

            elif multi_line_section.match(line):
                self._set_multiline_section(multi_line_section.sub(r'\1', line))

            else:
                self._add_to_current_section(line)


if __name__ == 'main':
    x = ArticleParser('Hello')
