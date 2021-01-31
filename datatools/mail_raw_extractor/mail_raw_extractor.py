# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import email
import re
import json
import pickle
import codecs
import getopt
from datetime import datetime
import locale
from dateutil import parser as dtparser
# from generic_modules.NameDetector import GenericNameDetector
# from generic_modules.DTPDetector import MLDateTimePhoneDetector, MLDateTimeEnricher
"""
Mail converter script

This script converts mails from .eml format to JSON. During this conversion, the *INITIAL* conversation
is identified and stored as the *ONLY* conversation. This script ignores any further conversation after
the initial one.

Only mails where the initial conversation was started by a 'customer' is stored.

Additionally, all emails are anoymized by removing footers, greetings, and by using a German firstnames
list to lookup if any word is a first name.

Copyright (c) 2019 Imdat Solak
              All rights reserved.

Usage:
    python convert_mails.py <indirectory> <outdirectory>

    - indirectory:      Contains mails in the eml (mbox)-format; one file per email
    - outdirectory:     An empty directory where the resulting json-files are written

Requires:
    - res/firstnames.txt:   A list of first names, one name per line
    - res/lastnames.txt:    A list of last names, one name per line

Written: 2017-02-06 00:00 CET, ISO
Updated: 2017-02-07 17:00 CET, ISO
         - Added new 'greetings'-lines (end_of_mail_lines) with additional German greetings
         - Fully anonymized the emails, including removing the original from and original to lines
"""


EMAIL_SUBS = u'__ANONYM_EMAIL__'
ZIP_CITY_SUBS = u'__ZIP_CITY__'
CENSOR_SUBS = u'__ANONYM__'
NUMBER_SUBS = u'__N__'
EMAIL_SUBS = u''
ZIP_CITY_SUBS = u''
CENSOR_SUBS = u''
NUMBER_SUBS = u''
checktokens = ['from:', 'von:', 'to:', 'an:', 'cc:', 'kopie:', 'kopie an:']
delheaders = ['message-id:', 'references:', 'cc:']
str2rep = ['<', '>', ' ', '[', ']', '&quot;', '=20', '<br>', '&lt;', '&gt;', '&quot;', '"', ',']
separators = ['-----Original-Nachricht-----', 'Ursprünglicher Text', '--- Original-Nachricht ---', '-----Original-Nachricht---','-----Ursprüngliche Mitteilung-----', '-----Ursprüngliche Nachricht-----', '------ Originalnachricht------', '------Originalnachricht------', '------ Originalnachricht ------', '------------------ Original ------------------']
stupid_sep = re.compile(r'[^A-z^0-9^\.^_]*([A-z0-9\.\-_]*@[A-z0-9\-]*\.[A-z0-9\-]*).*schrieb:')
stupid_sep2 = re.compile(r'<([A-z0-9\.\-_]*@[A-z0-9\-]*\.[A-z0-9\-]*)>.*schrieb:')
stupid_sep3 = re.compile(r'[^A-z^0-9^\.^_]*([A-z_\.0-9]+[A-z_\.0-9]*@[A-z\-0-9]+\.[A-z\-0-9]*).*wrote:')
stupid_sep4 = re.compile(r'schrieb [^A-z^0-9^\.^_]*([A-z0-9\.\-_]*@[A-z0-9\-]*\.[A-z0-9\-]*).*:')
stupid_sep5 = re.compile(r'Von: .*@imdat')
mail_addr_det = re.compile(r'[^A-z^0-9^\.^_]*([A-z_\.0-9]+[A-z_\.0-9]*@[A-z\-0-9]+\.[A-z\-0-9]*).*')
zip_city = re.compile(r'[0-9][0-9][0-9][0-9][0-9] [A-Z]+[a-z]*')
num_repl = re.compile(r'[0-9]+')

name_lines = ['sehr geehrte', 'dear ', 'hallo herr', 'hallo frau', 'guten tag']
end_of_mail_lines = ['mit freundlich', 'gruss', 'hochachtungsvoll', 'freundliche gr', 'freundlichen gr', 'mit besten gr', 'mit bestem gr', 'beste gr', 'besten gru', 'grüsse', 'gruss', 'gruß', 'gruesse', 'grüße', 'mfg', '-- ', '-------------------------------', 'viele grüße', 'viele grüsse', 'viele gruesse', 'viele grueße', 'freundlichen grüßen', 'freundlichen grüssen', 'freundlichen gruessen', 'vielen dank und viele grüße', 'vielen dank und viele gruesse', 'vielen dank und viele grüsse', 'ihre versandapotheke', 'mit den besten gr', 'mit freundl.', 'besten dank', 'danke und gr', 'von meinem android', 'von meinem iphone', 'von meinem samsung', 'von meinem huawei', 'von meinem sony', 'von meinem xperia', 'von meinem ipad', 'm.f.g.', 'danke und ein sch', 'gesendet von mail f', 'gesendet von yahoo', 'diese nachricht wurde von', 'ich habe diese nachricht mit der', 'gesendet mit der', '-------- weitergeleitete nachricht --------']
ignore_lines = ['vorname:', 'nachname:', 'adresse:']
header_keys = {'an':'To', 'von':'From', 'from':'From', 'to':'To', 'gesendet':'Sent', 'betreff':'Subject', 'sent':'Sent', 'subject':'Subject'}
OWN_DOMAINS = ['@imdat.de', '@imdat.com']
DEFAULT_US = 'service@imdat.de'
TO_US = 100
FROM_US = 200
UNKNOWN_DIRECTION = 300
MAX_HEADER_CHECK = 3
outdir = 'out'
FIRSTNAMES_FILE = 'res/firstnames.txt'
LASTNAMES_FILE = 'res/lastnames.txt'
LOCATIONS_FILE = 'res/de/locations.pickle'

firstnames = []
lastnames = []


def address_is_us(address):
    global OWN_DOMAINS
    address = address.lower()
    return any(domain in address.lower() for domain in OWN_DOMAINS)


class ASCIIMail:
    def __init__(self, message, source_filename):
        if message['From'] == DEFAULT_US:
            return None
        self.message = message
        self.mail_from = message['From']
        self.mail_to = message['To']
        self.source_filename = source_filename
        self.subject = message.get('Subject', '<NOSUBJECT>')
        self.to_censor = []
        self.mail_body = None


    def _is_in_nameslist(self, token, names_list):
        for name in names_list:
            if token == name:
                return True
        return False


    def _anonymize_line(self, line):
        global firstnames
        global lastnames
        global end_of_mail_lines

        line = line.strip()
        if mail_addr_det.match(line):
            line = mail_addr_det.sub(EMAIL_SUBS, line)
        if zip_city.match(line):
            line = zip_city.sub(ZIP_CITY_SUBS, line)
        l = ''
        for ch in line:
            if ch.isdigit():
                l += NUMBER_SUBS
            else:
                l += ch
        line = l

        tokens = line.split()
        for this_token in tokens:
            if len(this_token)<4:
                continue
            if this_token.lower() in self.mail_from.lower().split():
                self.to_censor.append(this_token)
                continue
            if self._is_in_nameslist(this_token, firstnames):
                if this_token not in self.to_censor:
                    self.to_censor.append(this_token)

        for token in self.to_censor:
            line = line.replace(token, CENSOR_SUBS)
        return line

    def _check_line_for_any_header(self, index, body, check_count=0, result_so_far=False):
        global MAX_HEADER_CHECK
        global header_keys

        if check_count > MAX_HEADER_CHECK:
            return result_so_far

        if index >= len(body):
            return result_so_far

        line = body[index]
        for header in header_keys:
            header_value = header_keys[header]
            header += ':'
            line = line.strip()
            lower_l = line.lower()
            if lower_l.startswith(header):
                if header_value == 'From':
                    self.part_mail_from = line.split(':')[1].strip()
                elif header_value == 'To':
                    self.part_mail_to = line.split(':')[1].strip()
                return self._check_line_for_any_header(index+1, body, check_count+1, True)
        return False


    def _is_part_separator(self, line, index, body):
        sm1 = stupid_sep.search(line)
        sm2 = stupid_sep2.search(line)
        sm4 = stupid_sep4.search(line)
        sm5 = stupid_sep5.search(line)
        if line in separators or sm1 or sm2 or sm4 or sm5:
            return True
        return self._check_line_for_any_header(index, body, 0)


    def _beautify_line(self, line):
        line = line.replace('\t', ' ')

        while '  ' in line:
            line = line.replace('  ', ' ')

        while '--' in line:
            line = line.replace('--', '')

        if line.startswith('> '):
            line = line[2:]

        if line.startswith('>'):
            line = line[1:]

        while '*' in line:
            line = line.replace('*', '')

        while '=' in line:
            line = line.replace('=', '')

        if line.startswith(' '):
            line = line[1:]

        if line.startswith('['):
            return ''

        if line.startswith('This e-mail'):
            return ''

        if line.startswith('--'):
            return ''

        if line.startswith('_'):
            return ''

        return line


    def parse(self):
        global DEFAULT_US

        contains_from_us = False

        text_to_parse = []
        mail_body = None
        mail_to = self.mail_to
        mail_from = self.mail_from
        for part in self.message.walk():
            if part.get_content_type() == 'text/plain':
                m = part.get_payload(None, True)
                charset = part.get_content_charset(None)
                if charset == None:
                    print('CHARSET -ERROR: {}'.format(m))
                else:
                    try:
                        if charset != 'utf-8':
                            mail_body = m.decode(charset.input_codec)
                        else:
                            mail_body = m
                        break
                    except:
                        pass
                        # print('Error decoding body {} '.format(m))

        if mail_body is not None:
            lines = mail_body.split('\n')
            mail_body = None
            for i, line in enumerate(lines):
                if line.startswith('_'):
                    line = line.replace('_', '', 1)
                if line.startswith('>'):
                    continue
                line = line.strip()
                if len(line) == 0:
                    continue
                if not self._is_part_separator(line, i, lines) and len(line)>0:
                    line = self._beautify_line(self._anonymize_line(line))
                    if len(line) > 0:
                        text_to_parse.append(line)

            self.mail_body = text_to_parse
        return (self.mail_body != None and len(self.mail_body) > 0)

    

    def getData(self):
        if self.mail_body is not None and len(self.mail_body) > 0:
            return { 'body': self.mail_body, 'subject': self._anonymize_line(self.subject)}
        return None


    def save(self, outfile):
        global TO_US
        global FROM_US
        mailBody = self.getData()
        if mailBody != None:
            try:
                json.dump(mailBody, codecs.open(outfile, 'w', 'utf-8'), indent=4)
            except:
                print('Could not save {} -> {}'.format(self.source_filename, outfile))
                pass

    
def parse_mails(indir, outdir, outfile):
    global firstnames
    global lastnames
    global locations
    firstnames = codecs.open(FIRSTNAMES_FILE, 'r', 'utf-8').read().split('\n')
    lastnames = codecs.open(LASTNAMES_FILE, 'r', 'utf-8').read().split('\n')
    locations = pickle.load(open(LOCATIONS_FILE, 'rb'))
    all_references = {}
    all_other = []

    print()
    print('************** M-AILABS  Mail Q-Generator for mbox-Format Emails ******************')
    print('           V1.0 - 2017-02-01, Copyright (c) 2019 Imdat Solak')
    print('                       Written: 2017-08-28, Imdat Solak')
    print('                             All rights reserved.')
    print('----------------------------------------------------------------------------------')
    if outdir != None and not os.path.exists(outdir):
        os.mkdir(outdir)
    # First collect all mails.
    # Some may contain references, others may not...
    print('Scanning directory %s... ' % indir, end='')
    filenames = []
    sys.stdout.flush()
    for root, dirs, files in os.walk(indir):
        for filename in filter(lambda filename: filename.endswith('.eml'), files):
            if not filename.startswith('._'):
                filenames.append(os.path.join(indir, filename))
    print('done')
    print('Parsing & Converting files, please wait...')
    result = []
    maxfiles = len(filenames)
    found_emails = 0
    total_emails = len(filenames)
    for i, filename in enumerate(filenames):
        if i % 50 == 0:
            print('{:-5d}/{}\r'.format(i, maxfiles), end='')
            sys.stdout.flush()
        raw_message = open(filename, 'r').read()
        msg = email.message_from_string(raw_message)
        mail = ASCIIMail(msg, filename)
        if mail.parse():
            mail.save(os.path.join(outdir, 'questions_{:06d}.json'.format(i)))
            found_emails += 1
            if outfile != None:
                mailData = mail.getData()
                if mailData != None and len(mailData.get('body', '')) > 0:
                    result.append(mailData)

    print('\ndone')
    print('Found {} emails to save (out of {} total emails) - saved to {}/*.json'.format(found_emails, total_emails, outdir))
    if outfile != None:
        outfile_dir = os.path.dirname(outfile)
        if not os.path.exists(outfile_dir):
            os.mkdir(outfile_dir)
        print('Saving TEXT File for Word2Vec Generation - this can take quite some time, please wait...', end='')
        sys.stdout.flush()
        text = ''
        with codecs.open(outfile, 'w', 'utf-8') as outfile:
            for mail in result:
                body = mail['body']
                subject = mail['subject']
                print(subject, file=outfile)
                for line in body:
                    line = line.strip()
                    if len(line) > 0:
                        print(line, file=outfile)

        print('done.')
    print('\nDONE')


def usage():
    print('Usage:')
    print('\tpython mail_raw_extractor.py -i|--indir <in-directory> -o|--outdir <out-dir>  [-f|--file]')
    print()
    print('\t\t-i <in-directory>: contains files ending in .eml to convert')
    print('\t\t-o <out-dir>     : the directory to save results to')
    print('\t\t-f               : also create a .txt-file containing all email bodies for Word2Vec')

    sys.exit(2)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:o:f', ['indir=', 'outdir=', 'file'])
    except getopt.GetoptError:
        usage()

    indir = None
    outdir = None
    outfile = None
    dumptxt = False
    for opt, arg in options:
        if opt in ('-i', '--indir'):
            indir = arg 
        elif opt in ('-o', '--outdir'):
            outdir = arg
        elif opt in ('-f', '--file'):
            dumptxt = True

    if indir != None and outdir != None:
        if dumptxt:
            outfile = os.path.join(outdir, 'outfile.txt')
        parse_mails(indir, outdir, outfile)
    else:
        usage()

