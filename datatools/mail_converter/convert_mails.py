# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
# import spacy
import email
import re
import json
import codecs
import getopt
from datetime import datetime
from progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
import locale
from dateutil import parser as dtparser
locale.setlocale(locale.LC_ALL, 'C')
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

Written: 2017-07-06 00:00 CET, ISO
Updated: 2017-07-07 17:00 CET, ISO
         - Added new 'greetings'-lines (end_of_mail_lines) with additional German greetings
         - Fully anonymized the emails, including removing the original from and original to lines
"""


checktokens = ['from:', 'von:', 'to:', 'an:', 'cc:', 'kopie:', 'kopie an:']
delheaders = ['message-id:', 'references:', 'cc:']
str2rep = ['<', '>', ' ', '[', ']', '&quot;', '=20', '<br>', '&lt;', '&gt;', '&quot;', '"', ',']
separators = ['-----Original-Nachricht-----', 'Ursprünglicher Text', '--- Original-Nachricht ---', '-----Original-Nachricht---','-----Ursprüngliche Mitteilung-----']
stupid_sep = re.compile(r'[^A-z^0-9^\.^_]*([A-z0-9\.\-_]*@[A-z0-9\-]*\.[A-z0-9\-]*).*schrieb:')
stupid_sep2 = re.compile(r'<([A-z0-9\.\-_]*@[A-z0-9\-]*\.[A-z0-9\-]*)>.*schrieb:')
stupid_sep3 = re.compile(r'[^A-z^0-9^\.^_]*([A-z_\.0-9]+[A-z_\.0-9]*@[A-z\-0-9]+\.[A-z\-0-9]*).*wrote:')
mail_addr_det = re.compile(r'[^A-z^0-9^\.^_]*([A-z_\.0-9]+[A-z_\.0-9]*@[A-z\-0-9]+\.[A-z\-0-9]*).*')
zip_city = re.compile(r'[0-9][0-9][0-9][0-9][0-9] [A-Z]+[a-z]*')
num_repl = re.compile(r'[0-9]+')

name_lines = ['sehr geehrte', 'dear ', 'hallo herr', 'hallo frau', 'guten tag']
end_of_mail_lines = ['mit freundlich', 'gruss', 'hochachtungsvoll', 'freundliche gr', 'freundlichen gr', 'mit besten gr', 'mit bestem gr', 'beste gr', 'besten gru', 'grüsse', 'gruss', 'gruß', 'gruesse', 'grüße', 'mfg', '-- ', '-------------------------------', 'viele grüße', 'viele grüsse', 'viele gruesse', 'viele grueße', 'freundlichen grüßen', 'freundlichen grüssen', 'freundlichen gruessen', 'vielen dank und viele grüße', 'vielen dank und viele gruesse', 'vielen dank und viele grüsse', 'ihre versandapotheke', 'mit den besten gr', 'mit freundl.', 'besten dank', 'danke und gr']
ignore_lines = ['vorname:', 'nachname:', 'adresse:']
header_keys = {'an':'To', 'von':'From', 'from':'From', 'to':'To', 'gesendet':'Sent', 'betreff':'Subject', 'sent':'Sent', 'subject':'Subject'}
OWN_DOMAINS = ['@m-ailabs.com', '@m-ailabs.eu']
DEFAULT_US = 'service@m-ailabs.com'
TO_US = 100
FROM_US = 200
UNKNOWN_DIRECTION = 300
MAX_HEADER_CHECK = 3
outdir = 'out'
FIRSTNAMES_FILE = 'res/firstnames.txt'
LASTNAMES_FILE = 'res/lastnames.txt'

firstnames = []
lastnames = []

def cleanup(data):
    retval = data.strip()
    for key in str2rep:
        retval = retval.replace(key, '')
    return retval.strip()


def address_is_us(address):
    global OWN_DOMAINS
    address = address.lower()
    return any(domain in address.lower() for domain in OWN_DOMAINS)


class ASCIIMailPart:
    def __init__(self, text, default_from=None, default_to=None):
        global UNKNOWN_DIRECTION
        self.text = text
        self.body = []
        self.headers = {}
        self.default_from = default_from
        self.default_to = default_to
        self.message_direction = UNKNOWN_DIRECTION

    def _is_greeting_line(self, line):
        global name_lines
        for entry in name_lines:
            if line.lower().startswith(entry):
                return True
        return False

    def _is_end_of_mail_line(self, line):
        global end_of_mail_lines
        for entry in end_of_mail_lines:
            if line.lower().startswith(entry):
                return True
        return False

    def _is_in_nameslist(self, token, names_list):
        for name in names_list:
            if token == name:
                return True
        return False

    def _anonymize_body(self):
        global firstnames
        global lastnames
        global end_of_mail_lines

        message_raw = self.body
        new_body = []
        self.body = []
        to_censor = []
        for line in message_raw:
            line = line.strip()
            if self._is_greeting_line(line):
                continue
            if self._is_end_of_mail_line(line):
                break
            if mail_addr_det.match(line):
                line = mail_addr_det.sub('__ANONYM_EMAIL__', line)
            tokens = line.split()
            if zip_city.match(line):
                line = zip_city.sub('__ZIP__CITY__', line)
            l = ''
            for ch in line:
                if ch.isdigit():
                    l += '__N__'
                else:
                    l += ch
            line = l
            for this_token in tokens:
                if len(this_token)<4:
                    continue
                if this_token.lower() in self.headers['From'].lower().split() or any(this_token.lower() in recip.lower().split() for recip in self.headers['To']) and not address_is_us(this_token):
                    # probably name or email, let's remove that
                    to_censor.append(this_token)
                    continue
                if self._is_in_nameslist(this_token, firstnames):
                    # it's a name, let's remove it
                    if this_token not in to_censor:
                        to_censor.append(this_token)
            
            new_body.append(line)

        for line in new_body:
            for token in to_censor:
                line = line.replace(token, '__ANONYM__')
            self.body.append(line)

    def parse(self):
        global header_keys
        global OWN_DOMAINS
        global TO_US
        global FROM_US

        temp_body = []
        searching_headers = True
        for line in self.text:
            line = line.strip()
            if len(line) == 0:
                if searching_headers == True:
                    searching_headers = False
                continue

            if ':' in line and searching_headers == True:
                header_key, header_value = line.split(':', 1)
                header_value = header_value.strip()
                header_key = header_key.lower()
                if header_key in header_keys.keys():
                    self.headers[header_keys[header_key]] = header_value
            elif searching_headers == False:
                self.body.append(line)
            else:
                temp_body.append(line)
        if self.headers.get('From', None) == None:
            self.headers['From'] = self.default_from
        if self.headers.get('To', None) == None:
            self.headers['To'] = self.default_to

        if len(self.body) == 0:
            self.body = temp_body

        if any(domain in self.headers['From'].lower() for domain in OWN_DOMAINS):
            self.message_direction = FROM_US
        else:
            self.message_direction = TO_US
        self._anonymize_body()

    def as_json(self):
        data_as_json = {'from': self.headers['From'], 'to': self.headers['To'], 'body': self.body}
        return data_as_json

    def dump(self, outfile=sys.stdout):
        print('Part-From: ', self.headers['From'], file=outfile)
        print('Part-To  : ', self.headers['To'], file=outfile)
        print('Body     : ', self.body, file=outfile)
        print('-------------------------------------------- EOT -----------------------------------------------', file=outfile)


class ASCIIMail:
    def __init__(self, message, out_filename):
        self.message = message
        self.mail_from = message['From']
        self.mail_to = message['To']
        date_info = message.get('Date', None)
        if date_info != None:
            try:
                self.mail_datetime = dtparser.parse(date_info)
            except:
                print('Weird date-time [%s]' % date_info)
                self.mail_datetime = None
        self.parts = []
        self.part_mail_to = ''
        self.part_mail_from = ''
        self.references = []
        self.out_filename = out_filename

        self.reference = None
        ref = message.get('References', None)
        if ref != None:
            references = ref.split()
            if len(references)>0:
                ref = references[0]
                ref = ref.replace('>', '')
                ref = ref.replace('<', '')
                ref = ref.replace(',', '')
                self.reference = ref.strip()

    def _fix_headers(self):
        global mail_addr_det
        mail_to = None
        if self.mail_to != None:
            mail_to = self.mail_to.split('\n')
        if self.mail_from != None:
            mail_from = mail_addr_det.sub(r'\1', self.mail_from)
        else:
            mail_from = ''
        recipients = []
        if mail_to != None and len(mail_to) > 1:
            for recipient in mail_to:
                email_addr = mail_addr_det.sub(r'\1', recipient)
                if email_addr == mail_from: # The user has "cc'd" himself (stupid user)
                    continue
                recipients.append(email_addr)
        elif mail_to != None:
            email_addr = mail_addr_det.sub(r'\1', mail_to[0])
            recipients.append(email_addr)
        self.mail_to = recipients

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
        if line in separators or sm1 or sm2:
            return True
        return self._check_line_for_any_header(index, body, 0)

    def parse(self):
        global separators
        global stupid_sep
        global stupid_sep2
        global DEFAULT_US

        self._fix_headers()
        text_to_parse = []
        mail_body = ''
        mail_to = self.mail_to
        mail_from = self.mail_from
        for part in self.message.walk():
            if part.get_content_type() == 'text/plain':
                mail_body += part.get_payload(None, True)

        lines = mail_body.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('_'):
                line = line.replace('_', '', 1)
            if line.startswith('>'):
                line = line.replace('>', '', 1)
            line = line.strip()
            if len(line) == 0:
                continue
            if self._is_part_separator(line, i, lines):
                current_part = ASCIIMailPart(text_to_parse, mail_from, mail_to)
                current_part.parse()
                self.parts.append(current_part)
                text_to_parse = []
                sm1 = stupid_sep.search(line)
                sm2 = stupid_sep2.search(line)
                if sm1:
                    who_wrote = stupid_sep.sub(r'\1', line)
                    if not address_is_us(who_wrote):
                        mail_from = who_wrote
                        mail_to = DEFAULT_US
                    else:
                        mail_from = DEFAULT_US
                        mail_to = who_wrote
                elif sm2:
                    who_wrote = stupid_sep2.sub(r'\1', line)
                    if not address_is_us(who_wrote):
                        mail_from = who_wrote
                        mail_to = DEFAULT_US
                    else:
                        mail_from = DEFAULT_US
                        mail_to = who_wrote
                else:
                    mail_from = self.part_mail_from
                    mail_to = self.part_mail_to
                    self.part_mail_from = ''
                    self.part_mail_to = ''
            elif not any(line.lower().startswith(lti) for lti in ignore_lines):
                text_to_parse.append(line)

        if len(text_to_parse) > 0:
            current_part = ASCIIMailPart(text_to_parse, mail_from, mail_to)
            current_part.parse()
            self.parts.append(current_part)
    
    def append_reference(self, a_reference):
        if a_reference != None:
            self.references.append(a_reference)

    def reset_parts(self, new_parts):
        self.parts = new_parts

    def parse_references(self):
        if len(self.references) == 0:
            return self
        mails_sorted = []
        mails_unsorted = []
        mails_unsorted.append(self)
        mails_unsorted.extend(self.references)
        mails_sorted = sorted(mails_unsorted, key=lambda item: item.mail_datetime.strftime('%Y%m%d%H%M%S')) # The oldest one is at index=0
        new_parts = []
        for mail in mails_sorted:
            new_parts.extend(mail.parts)

        self.reset_parts(new_parts)
        return self

    def dump(self, outfile=sys.stdout):
        print('From: ', self.mail_from, file=outfile)
        print('To  : ', self.mail_to, file=outfile)
        print('PARTS.....................................................................', file=outfile)
        for part in self.parts:
            part.dump(outfile)

    def save(self):
        global TO_US
        global FROM_US
        if len(self.parts) > 1:
            # The message parts are sorted, the oldest being at the last index in our array.
            # Incidentially, the oldest is also (hopefully) the original request from the customer
            initial_message = self.parts[-1]
            response_to_initial_message = self.parts[-2]
            if initial_message.message_direction == TO_US:
                index = len(self.parts)-2
                while response_to_initial_message.message_direction != FROM_US and index>0:
                    index -= 1
                    if index < len(self.parts):
                        response_do_initial_message = self.parts[index]
                if response_to_initial_message.message_direction == FROM_US:
                    question = initial_message.as_json()
                    response = response_to_initial_message.as_json()
                    # if we are missing the question or the answer, we can't do anything with this data...
                    if len(question['body']) > 0 and len(response['body']) > 0:
                        qa_pair = {'question' : question['body'], 'answer': response['body']}
                        json.dump(qa_pair, codecs.open(self.out_filename, 'w', 'utf-8'), indent=4)


def parse_mails(indir, outdir):
    global firstnames
    global lastnames
    firstnames = open(FIRSTNAMES_FILE, 'r').read().split('\n')
    lastnames = open(LASTNAMES_FILE, 'r').read().split('\n')
    all_references = {}
    all_other = []

    print()
    print('****************** Mail Converter for mbox-Format Emails ************************')
    print('     V1.0 - 2017-08-01, Copyright (c) 2017 MUNICH AILABS GmbH')
    print('                   Written: 2017-08-01 ... 15, Imdat Solak')
    print('                            All rights reserved.')
    print('----------------------------------------------------------------------------------')
    print()
    if not os.path.exists(outdir):
        os.mkdir(outdir)
    # First collect all mails.
    # Some may contain references, others may not...
    print('Scanning directory [%s]... ' % indir, end='')
    filenames = []
    sys.stdout.flush()
    for root, dirs, files in os.walk(indir):
        for filename in filter(lambda filename: filename.endswith('.eml'), files):
            if not filename.startswith('._'):
                filenames.append(os.path.join(indir, filename))
    print('done')
    print('Parsing files...')
    widgets=[FormatLabel('File: [%(value)s/'+str(len(filenames))+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'), ' ', ETA()]

    pBar = ProgressBar(widgets=widgets, maxval=len(filenames)).start()
    for i, filename in enumerate(filenames):
        pBar.update(i, '')
        raw_message = codecs.open(filename, 'r', 'utf-8').read()
        msg = email.message_from_string(raw_message)
        mail = ASCIIMail(msg, os.path.join(outdir, os.path.basename(filename) + '.json'))
        mail.parse()
        if mail.reference != None:
            if all_references.get(mail.reference, None) == None:
                all_references[mail.reference] = mail
            else:
                all_references[mail.reference].append_reference(mail)
        else:
            all_other.append(mail)

    pBar.finish()
    print('Merging mails...')
    widgets=[FormatLabel('File: [%(value)s/'+str(len(all_references.keys()))+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'), ' ', ETA()]
    pBar = ProgressBar(widgets=widgets, maxval=len(all_references.keys())).start()
    # Now check for references...
    for i, a_ref in enumerate(all_references.keys()):
        pBar.update(i, '')
        amail = all_references[a_ref].parse_references()
        all_other.append(amail)

    pBar.finish()
    all_references = {}

    # Now save the found emails...
    print('Saving files... ', end='')
    sys.stdout.flush()
    for amail in all_other:
        amail.save()
    print('done)')


def usage():
    print('Usage:')
    print('\tpython convert_mails.py -i|--indir <in-directory> -o|--outdir <out-directory>')
    sys.exit(2)


try:
    options, arguments = getopt.getopt(sys.argv[1:], 'i:o:', ['indir=', 'outdir='])
except getopt.GetoptError:
    usage()

indir = None
outdir = None
for opt, arg in options:
    if opt in ('-i', '--indir'):
        indir = arg 
    elif opt in ('-o', '--outdir'):
        outdir = arg

if indir != None and outdir != None:
    parse_mails(indir, outdir)
else:
    usage()

