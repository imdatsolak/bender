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
mail_addr_det = re.compile(r'[^A-z^0-9^\.^_]*([A-z_\.0-9]+[A-z_\.0-9]*@[A-z\-0-9]+\.[A-z\-0-9]*).*')
zip_city = re.compile(r'[0-9][0-9][0-9][0-9][0-9] [A-Z]+[a-z]*')
num_repl = re.compile(r'[0-9]+')

name_lines = ['sehr geehrte', 'dear ', 'hallo herr', 'hallo frau', 'guten tag]
end_of_mail_lines = ['mit freundlich', 'gruss', 'hochachtungsvoll', 'freundliche gr', 'freundlichen gr', 'mit besten gr', 'mit bestem gr', 'beste gr', 'besten gru', 'grüsse', 'gruss', 'gruß', 'gruesse', 'grüße', 'mfg', '-- ', '-------------------------------', 'viele grüße', 'viele grüsse', 'viele gruesse', 'viele grueße', 'freundlichen grüßen', 'freundlichen grüssen', 'freundlichen gruessen', 'vielen dank und viele grüße', 'vielen dank und viele gruesse', 'vielen dank und viele grüsse', 'ihre versandapotheke', 'mit den besten gr', 'mit freundl.', 'besten dank', 'danke und gr', 'von meinem android', 'von meinem iphone', 'von meinem samsung', 'von meinem huawei', 'von meinem sony', 'von meinem xperia', 'von meinem ipad', 'm.f.g.', 'danke und ein sch', 'gesendet von mail f', 'gesendet von yahoo', 'diese nachricht wurde von', 'ich habe diese nachricht mit der', 'gesendet mit der', '-------- weitergeleitete nachricht --------']
ignore_lines = ['vorname:', 'nachname:', 'adresse:']
header_keys = {'an':'To', 'von':'From', 'from':'From', 'to':'To', 'gesendet':'Sent', 'betreff':'Subject', 'sent':'Sent', 'subject':'Subject'}
OWN_DOMAINS = ['@imdat.de', '@solak.de']
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
            # if self._is_end_of_mail_line(line):
             #    break
            if mail_addr_det.match(line):
                line = mail_addr_det.sub(EMAIL_SUBS, line)
            tokens = line.split()
            if zip_city.match(line):
                line = zip_city.sub(ZIP_CITY_SUBS, line)
            l = ''
            for ch in line:
                if ch.isdigit():
                    l += NUMBER_SUBS
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
                if self._is_in_nameslist(this_token, firstnames) or self._is_in_nameslist(this_token, lastnames):
                    # it's a name, let's remove it
                    if this_token not in to_censor:
                        to_censor.append(this_token)
            
            new_body.append(line)

        for line in new_body:
            for token in to_censor:
                line = line.replace(token, CENSOR_SUBS)
            self.body.append(line)


    def parse(self):
        global header_keys
        global OWN_DOMAINS
        global TO_US
        global FROM_US

        temp_body = []
        searching_headers = True
        for line in self.text:
            # line = line.strip()
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
    def __init__(self, message, source_filename):
        self.message = message
        self.mail_from = message['From']
        self.mail_to = message['To']
        self.source_filename = source_filename
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
        sm4 = stupid_sep4.search(line)
        if line in separators or sm1 or sm2 or sm4:
            return True
        return self._check_line_for_any_header(index, body, 0)


    def parse(self):
        global separators
        global stupid_sep
        global stupid_sep2
        global stupid_sep4
        global DEFAULT_US

        self._fix_headers()
        text_to_parse = []
        mail_body = ''
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

        lines = mail_body.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('_'):
                line = line.replace('_', '', 1)
            if line.startswith('>'):
                continue
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
                sm4 = stupid_sep4.search(line)
                if sm1:
                    sm = sm1
                    who_wrote = stupid_sep.sub(r'\1', line)
                elif sm2:
                    sm = sm2
                    who_wrote = stupid_sep2.sub(r'\1', line)
                elif sm4:
                    who_wrote = stupid_sep4.sub(r'\1', line)
                    sm = sm4
                else:
                    sm = None
                if sm != None:
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

    
    def dump(self, outfile=sys.stdout):
        print('From: ', self.mail_from, file=outfile)
        print('To  : ', self.mail_to, file=outfile)
        print('PARTS.....................................................................', file=outfile)
        for part in self.parts:
            part.dump(outfile)


    def getData(self):
        global TO_US
        global FROM_US
        if len(self.parts) >= 1:
            question = []
            for part in self.parts:
                body_text = part.as_json()
                question.append(body_text['body'])
            return question
        return None


    def save(self, outfile):
        global TO_US
        global FROM_US
        qa_pair = self.getData()
        if qa_pair != None:
            try:
                json.dump(qa_pair, codecs.open(outfile, 'w', 'utf-8'), indent=4)
            except:
                print('Could not save {} -> {}'.format(self.source_filename, outfile))
                pass



def cleanup(line):
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
    for i, filename in enumerate(filenames):
        if i % 50 == 0:
            print('{:-5d}/{}\r'.format(i, maxfiles), end='')
            sys.stdout.flush()
        raw_message = open(filename, 'r').read()
        msg = email.message_from_string(raw_message)
        mail = ASCIIMail(msg, filename)
        mail.parse()
        if (outdir != None):
            mail.save(os.path.join(outdir, 'questions_{:06d}.json'.format(i)))
        else:
            mailData = mail.getData()
            if mailData != None and len(mailData) > 0:
                result.append(mailData)

    print('\ndone')
    if outfile != None:
        outfile_dir = os.path.dirname(outfile)
        if not os.path.exists(outfile_dir):
            os.mkdir(outfile_dir)
        print('Saving file... ', end='')
        sys.stdout.flush()
        text = ''
        for mail in result:
            for part in mail:
                if isinstance(part, basestring):
                    part = cleanup(part)
                    if part != None and part != '':
                        text = text + '\n' + part
                else:
                    for line in part:
                        line = cleanup(line)
                        if line != None and line != '':
                            text = text + '\n' + line

        # json.dump(result, codecs.open(outfile, 'w', 'utf-8'), indent=4)
        with codecs.open(outfile, 'w', 'utf-8') as f:
            print(text, file=f)

        print('done.')
    print('\nDONE')


def usage():
    print('Usage:')
    print('\tpython convert_mails.py -i|--indir <in-directory> <[-o|--outdir] | [-O|--outfile]>')
    sys.exit(2)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:o:O:', ['indir=', 'outdir=', 'outfile='])
    except getopt.GetoptError:
        usage()

    indir = None
    outdir = None
    outfile = None
    for opt, arg in options:
        if opt in ('-i', '--indir'):
            indir = arg 
        elif opt in ('-o', '--outdir'):
            outdir = arg
        elif opt in ('-O', '--outfile'):
            outfile = arg

    if indir != None and (outdir != None or outfile != None):
        parse_mails(indir, outdir, outfile)
    else:
        usage()

