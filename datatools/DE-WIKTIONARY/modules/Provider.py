# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

# Copyright (c) 2004 Guaka
# Copyright (c) 2017 Munich Artificial Intelligence Laboratories GmbH
# Written: 2017-??-?? ??:?? CET, ISO
#          - Based on wik2dict's Provider-Class
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
wik2dict's Provider classes.

These are an abstraction of wik2dict's retrieval mechanism.
Currently lacking a MySQL Provider.
"""
#
import os
import re
import bz2, gzip
from sets import Set

import pprint
import xml.etree.ElementTree as ET

mwxml = "{http://www.mediawiki.org/xml/export-0.10/}"

class XMLfile_Provider:
  def __init__(self, filename):
	self.filename = filename
	self.tree = ET.parse(filename)

	self.nr_articles = 0
	self.article_titles = Set()
	self.article_redirects = {}
	self.articles = {}
	self.messages = {}
	self.message_redirects = {}
	self.meta_info = {}
	self.categories = {}

	self.namespaces = self._get_namespaces()

	x_pages = self.tree.findall(mwxml + "page")
	for x_page in x_pages:
		title = x_page.find(mwxml + "title").text
		text = x_page.find(mwxml + "revision").find(mwxml + "text").text
		ns, ns_name = 0, ""
		for ns_text in self.namespaces:
			if title[:len(ns_text)] == ns_text:
				ns = self.namespaces[ns_text]
				nsname = ns_text
		if ns == 0:
			self.articles[title] = text
		elif ns == 8:
			self.messages[title] = text
		elif ns == 14:
			self.categories[title] = text

  def _get_namespaces(self):
	namespaces = {}
	x_siteinfo = self.tree.find(mwxml + "siteinfo")
	x_namespaces = x_siteinfo.find(mwxml + "namespaces")
	for x_ns in x_namespaces:
		if x_ns.text is None:
			namespaces[""] = int(x_ns.get('key'))
		else:
			namespaces[x_ns.text] = int(x_ns.get('key'))
	return namespaces


