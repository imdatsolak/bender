# -*- coding: utf-8 -*-
from __future__ import print_function
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import re
import codecs
from datetime import datetime, timedelta
from dateutil import parser as dtparser
"""
Data Detectors

This module is used to detect special data in requests such as dates, times, phone-numbers, addresses, and more...

Using the class MLDateTimePhoneDetector, you can detect the data in line of text.
There is only one public method:
    def detectDataInText(origjnalText)

It will return either 'None' or an array of items found. This array is sorted (first entry is the first
found data)

The data is a dictionary containing following items:
    'location' : the location (begin, end) as a tuple of the data detected
    'found'    : what was found there (original text)
    'type'     : one of PIT
                    PIT = Point In Time
                    PIT_NOW =  Point In Time (Today)
                    PIT_NOW+SPECIAL =  Point In Time (Today) - usually something like 'today', 'today afternoon', ...
                    TIME_FRAME = A timeframe, e.g., 01. Jan - 12. Feb 2017
                    PHONE =  A phone
                    PIT_PAST = A Point in Time in the PAST
                    PIT_FUTURE = A Point in Time in the FUTURE
    'converted': the converted value of the data that was found.

    In converted, you usually find (in case of date/time) a datetime (AS STIRNG) in ISO-Notation but local-time
    If the converted time is a TIME_FRAME, you will find 'FROM_TO', both in ISO-Notation
    I don't know yet what we will show in telephone numbers :-)

If you use the MLDateTimeEnricher, which also has a single public method, you can ask it to enrich your
text.

It will then enclose EVERY FOUND text with a [ ] - and append "MLIsData=" after it. After the equal-sign,
you can then find the actual 'converted'-data. This is useful for various task, but you don't *have* to use
MLDateTimeEnricher if you want to do that stuff yourself...

For testing purposes, add a text-file (preferably in german) named 'test.txt' in the same folder as this
module and run it without any paramters:
    python datadetector.py

You will then see, for each line in the test.txt, something like this:
    am 20.12.16 habe ich eine "Kommen" Buchung zu viel in myPortal hinterlegt
    am [20.12.16 MLIsData=2016-12-20 00:00] habe ich eine "Kommen" Buchung zu viel in myPortal hinterlegt
    ********************************************************************************

The first line is the original, and the second the enriched version...
Have fun...

Written: 2017-05-24 14:21 CET, ISO
Updated: 2017-05-26 14:23 CET, ISO
         Initial fully functioning version (tested with German)
"""

# AUXILIARY Functions

def utcize_date(entry):
    found = False
    for lang, entries in calendar_months_long.iteritems():
        for month, mnum in entries.iteritems():
            if month in entry:
                pos = entry.index(month)
                entry = entry[:pos] + calendar_months_UTC_long[mnum-1] + entry[pos+len(month):]
                found = True
            if found:
                break
        if found:
            break
            
    for lang, entries in calendar_months_short.iteritems():
        for month, mnum in entries.iteritems():
            if month in entry:
                pos = entry.index(month)
                entry = entry[:pos] + calendar_months_UTC_long[mnum-1] + entry[pos+len(month):]
                found = True
            if found:
                break
        if found:
            break
    return entry

def utcize_date_add_year(entry):
    entry = utcize_date(entry)
    entry = entry + ' ' + str(datetime.now().year)
    return entry

def utcize_date_add_day(entry):
    entry = utcize_date(entry)
    entry = '01. '+entry
    return entry

def add_year(entry):
    if entry[len(entry)-1] != '.':
        entry = entry + '.'
    entry = entry + str(datetime.now().year)
    return entry

def replace_words_utcize_date(entry):
    found = False
    for lang, entries in word_meanings_month.iteritems():
        for word, values in entries.iteritems():
            if word in entry:
                pos = entry.index(word)
                entry = entry[:pos] + str(values) + '.' + entry[pos+len(word):]
                found = True
            if found:
                break
        if found:
            break

    return utcize_date(entry)

def replace_words_utcize_date_add_year(entry):
    entry = replace_words_utcize_date(entry)
    entry = entry + ' ' + str(datetime.now().year)
    return entry

def get_today_morning(entry):
    # Mmorning is between 4am and 10am
    now = datetime.now()
    actual_time = datetime(now.year, now.month, now.day, 4, 0, 0)
    return actual_time.strftime('%Y-%m-%d %H:%M')

def get_today_noon(entry):
    # Noon is between 10am and 2pm
    now = datetime.now()
    actual_time = datetime(now.year, now.month, now.day, 10, 0, 0)
    return actual_time.strftime('%Y-%m-%d %H:%M')

def get_today_afternoon(entry):
    # Afternoon is between 2pm and 5pm
    now = datetime.now()
    actual_time = datetime(now.year, now.month, now.day, 14, 0, 0)
    return actual_time.strftime('%Y-%m-%d %H:%M')

def get_today_evening(entry):
    # Evening is between 5pm and 10pm
    now = datetime.now()
    actual_time = datetime(now.year, now.month, now.day, 17, 0, 0)
    return actual_time.strftime('%Y-%m-%d %H:%M')

def get_today_night(entry):
    # Night is between 10pm and 12pm
    now = datetime.now()
    actual_time = datetime(now.year, now.month, now.day, 22, 0, 0)
    return actual_time.strftime('%Y-%m-%d %H:%M')

# The representation of months in UTC-Format (do NOT TOUCH)
calendar_months_UTC_short = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
calendar_months_UTC_long = ['January', 'February', 'March', 'April', 'May', 'June', 'Juli', 'August', 'September', 'October', 'November', 'December']

#
# LOTS of array, dictionaries, regular expressions and so forth.
# The following are month-names in three languages. You MUST add your language here as shown.
#
calendar_months_long = {
        'de': {'januar': 1, 'februar': 2, 'maerz':3, 'marz':3, 'märz': 3, 'april': 4, 'mai': 5, 'juni': 6, 'juli': 7, 'august': 8, 'september':9, 'oktober':10, 'november': 11, 'dezember': 12},
        'en': {'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6, 'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12},
        'tr': {'ocak': 1, 'subat': 2, 'şubat': 2, 'mart': 3, 'nisan': 4, 'mayis': 5, 'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'augustos': 8, 'auğustos': 8, 'eylül': 9, 'eylul':9, 'ekim': 10, 'kasım': 11, 'kasim': 11, 'aralık': 12, 'aralik': 12}}

calendar_months_short = {
        'de': {'jan': 1, 'feb': 2, 'mae': 3, 'mar': 3, 'mär': 3, 'apr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'okt': 10, 'nov':11, 'dez':12},
        'en': {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12},
        'tr': {'oca': 1, 'sub': 2, 'şub': 2, 'mar': 3, 'nis': 4, 'may': 5, 'haz': 6, 'tem': 7, 'aug': 8, 'auğ': 8, 'eyl': 9, 'eki': 10, 'kas': 11, 'ara': 12}}

# Weekdays
weekdays = {
        'de': {'montag': 1, 'dienstag': 2, 'mittwoch': 3, 'donnerstag': 4, 'freitag': 5, 'samstag': 6, 'sonnabend': 6, 'sonntag': 7},
        'en': {'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4, 'friday': 5, 'saturday': 6, 'sunday': 7},
        'tr': {'pazartesi': 1, 'sali': 2, 'salı': 2, 'carsamba':3, 'çarsamba': 3, 'carşamba': 3, 'çarşamba': 3, 'persembe': 4, 'perşembe': 4, 'cuma': 5, 'cumartesi': 6, 'pazar': 7}}


word_meanings_month = {
        'de': {'anfang': 1, 'mitte': 15, 'ende': 28},
        'en': {'begin': 1, 'mid': 15, 'end': 28},
        'tr': {'bas': 1, 'orta': 15, 'son': 28}
        }
# NOTE: on the following RegExps, the order in the array is important as the longest detection should
# happen BEFORE the shorter detection of similar RegExps!!


date_detectors = [
        # Detects [0]1. Januar [20]17
        { 
            'regex': re.compile(r'[0-2]{0,1}[0-9].[ ]+\b(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez)\b[ ,]{0,1}[2]{0,1}[0]{0,1}[1-3][0-9]'),
            'pre_code': lambda entry: utcize_date(entry)
        },
        # Detects [0]1. Januar
        {
            'regex': re.compile(r'[0-2]{0,1}[0-9].[ ]+\b(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez)\b'),
            'pre_code': lambda entry: utcize_date_add_year(entry)
        },
        # Detects [0]1.[0]1.[20]17
        {
            'regex': re.compile(r'[0-3]{0,1}[0-9]\.[0-3]{0,1}[0-9]\.[2]{0,1}[0]{0,1}[1-3][0-9]'),
            'pre_code': lambda entry: entry
        },
        # Detects 'Dezember [20]17'
        {
            'regex': re.compile(r'(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez)[ ]+[2]{0,1}[0]{0,1}[0-3]{0,1}[0-9]'),
            'pre_code': lambda entry: utcize_date_add_day(entry)
        },
        # Detects [0]1.[0]1.
        {
            'regex': re.compile(r'[0-3]{0,1}[0-9]\.[0-3]{0,1}[0-9]\.'),
            'pre_code': lambda entry: add_year(entry)
        },
        # Detects 'Anfang|Ende|Mitte Dezember [20]17'
        {
            'regex': re.compile(r'\b(anfang|mitte|ende)\b (januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez)[ ]+[2]{0,1}[0]{0,1}[0-3]{0,1}[0-9]'),
            'pre_code': lambda entry: replace_words_utcize_date(entry)
        },
        # Detects 'Anfang|Ende|Mitte Dezember'
        {
            'regex': re.compile(r'\b(anfang|mitte|ende)\b \b(januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez)\b'),
            'pre_code': lambda entry: replace_words_utcize_date_add_year(entry)
        }
        ]

# DATE-FRAME (TIME-FRAME) detectors. They are used to detect time-frames given e.g. as "01.01.-05.01.2017"
time_frame_detectors = [
        # Detects [0]1.[0]1.[20]17-[0]5.[0]5.[20]17
        re.compile(r'[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9]\.[ ]*[2]{0,1}[0]{0,1}[1-3]{0,1}[0-9][\.]{0,1}[ ]*-[ ]*[0-3]{0,1}[0-9]\.[0-2]{0,1}[0-9]\.[ ]*[2]{0,1}[0]{0,1}[1-3][0-9]'), 
        # Detects [0]1.[0]1.-[0]5.[0]5.[20]17
        re.compile(r'[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9][\.]{0,1}[ ]*-[ ]*[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9]\.[ ]*[2]{0,1}[0]{0,1}[1-3][0-9]'), 
        # Detects [0]1.[0]1[.]-[0]5.[0]5
        re.compile(r'[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9][\.]{0,1}[ ]{0,1}-[ ]{0,1}[0-3]{0,1}[0-9]\.[0-1]{0,1}[0-9][\.]{0,1}'), 
        # Detects [0]1.Jan [20]17 - [0]5. Mai [20]17
        re.compile(r'[0-2]{0,1}[0-9][. ]{0,1}[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez][ ,]{0,1}[2]{0,1}[0]{0,1}[1-3][0-9][ ]{0,1}-[ ]{0,1}[0-2]{0,1}[0-9].[ ]+[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez][ ,]{0,1}[2]{0,1}[0]{0,1}[1-3][0-9]'), 
        # Detects [0]1.Jan - [0]5. Mai [20]17
        re.compile(r'[0-2]{0,1}[0-9][. ]{0,1}[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez][ ]{0,1}-[ ]{0,1}[0-2]+[0-9].[ ]+[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez][ ,]{0,1}[2]{0,1}[0]{0,1}[1-3][0-9]'), 
        # Detects [0]1.Jan - [0]5. Mai
        re.compile(r'[0-2]{0,1}[0-9].[ ]{0,1}[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez][ ]{0,1}-[ ]{0,1}[0-3]{0,1}[0-9].[ ]{0,1}[januar|februar|märz|april|mai|juni|juli|august|september|oktober|november|dezember|jan|feb|mär|mar|apr|mai|jun|jul|aug|sep|okt|nov|dez]') ]

# The following are detectors for "today" nor "now"
# Depending on the language, you should normally check for "_special" first (that is what
# we do here for GERMAN & ENGLISH. 
pit_detectors_now = [re.compile(r'heute'), re.compile(r'jetzt')]
pit_detectors_now_special = [
        {'regex': re.compile(r'heute morgen'), 'code': lambda entry: get_today_morning(entry)},
        {'regex': re.compile(r'heute \b(mittag|mittags)\b'), 'code': lambda entry: get_today_noon(entry)},
        {'regex': re.compile(r'heute nachmittag'), 'code': lambda entry: get_today_afternoon(entry)},
        {'regex': re.compile(r'heute abend\b'), 'code': lambda entry: get_today_evening(entry)},
        {'regex': re.compile(r'\bheute nacht\b'), 'code': lambda entry: get_today_night(entry)} ]


# Please look at the syntax clearly:
# The date mentioned is calculated depending on 'dim':
#   - dim = hours:  add/subtract hours * seconds
#   - dim = days:   add/subtract days * 24 * seconds
#   - dim = weeks:  add/subtract weeks * 7 * 24 * seconds
#   - dim = months: add/subtract months * 31 * 24 * seconds
#   - dim = years:  add/subtract years * 365 * 24 * seconds
# NOTE: in some cases the actual "number" is extracted from the text

# The following are detectors for time in the past
pit_detectors_past = [ 
        {'date': -48, 'dim': 'hours', 'regex': re.compile(r'\bvorgestern\b')},
        {'date': -24, 'dim': 'hours', 'regex': re.compile(r'\bgestern\b')},
        {'date': 0, 'dim': 'days_extracted', 'regex': re.compile(r'vor ([\d]+) tag')},
        {'date': 0, 'dim': 'days_extracted', 'regex': re.compile(r'vor (ein|einem|einen|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf|dreizehn|vierzehn) tag')},
        {'date': 0, 'dim': 'weeks_extracted', 'regex': re.compile(r'vor ([\d]+)\b(woche)')},
        {'date': -1, 'dim': 'weeks', 'regex': re.compile(r'(vorige|voriger|vorigen|vorigem|vorig) woche')},
        {'date': 0, 'dim': 'weeks_extracted', 'regex': re.compile(r'vor (eine|einer|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) woche')},
        {'date': -1, 'dim': 'months', 'regex': re.compile(r'(vorigen|vorigem|vorige|vorig) monat')},
        {'date': 0, 'dim': 'months_extracted', 'regex': re.compile(r'vor ([\d]+) monat')},
        {'date': 0, 'dim': 'months_extracted', 'regex': re.compile(r'vor (eine|einer|einem|einen|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) monat')},
        {'date': -1, 'dim': 'years', 'regex': re.compile(r'(vorigen|vorigem|vorige|vorig|voriges) jahr')},
        {'date': 0, 'dim': 'years_extracted', 'regex': re.compile(r'vor ([\d]+) jahr')},
        {'date': 0, 'dim': 'years_extracted', 'regex': re.compile(r'vor (eine|einer|einem|einen|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) jahr')} ]

pit_terms_to_nums = {
        'de': {
            'ein': 1, 'zwei': 2, 'drei': 3, 'vier': 4, 'fünf': 5, 'fuenf': 5, 'sechs': 6, 'sieben': 7, 'acht': 8, 'neun': 9, 'zehn': 10, 'vorig': 1},
        'en': {
            'a': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10},
        'tr': {
            'bir': 1, 'iki': 2, 'üç': 3, 'uc': 3, 'dört': 4, 'dort': 4, 'beş': 5, 'bes': 5, 'altı': 6, 'alti': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9, 'on': 10 }
        }

# The following are detectors for time in the future
pit_detectors_future = [ 
        {'date': 48, 'dim': 'hours', 'regex': re.compile(u'(übermorgen|uebermorgen|ueber morgen)')},
        {'date': 24, 'dim': 'hours', 'regex': re.compile(r'\b(^guten)\bmorgen\b')},
        {'date': 0, 'dim': 'days_extracted', 'regex': re.compile(r'in ([\d]+) tag')},
        {'date': 0, 'dim': 'days_extracted', 'regex': re.compile(r'in (ein|einem|einen|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|elf|zwölf|zwoelf|dreizehn|vierzehn) tag')},
        {'date': 2, 'dim': 'weeks', 'regex': re.compile(u'(übernächste|uebernaechste)[snm]{0,1} woche')},
        {'date': 1, 'dim': 'weeks', 'regex': re.compile(u'(nächste|naechste)[snm]{0,1} woche')},
        {'date': 0, 'dim': 'weeks_extracted', 'regex': re.compile(r'in ([\d]+) woche')},
        {'date': 0, 'dim': 'weeks_extracted', 'regex': re.compile(r'in (eine|einer|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) woche')},
        {'date': 2, 'dim': 'months', 'regex': re.compile(u'(übernächste|uebernaechste)[snm]{0,1} monat')},
        {'date': 1, 'dim': 'months', 'regex': re.compile(u'(nächste|naechste)[smn]{0,1} monat')},
        {'date': 1, 'dim': 'months', 'regex': re.compile(r'in ([\d]+) monat')},
        {'date': 0, 'dim': 'months_extracted', 'regex': re.compile(r'in ([\d]+) monat')},
        {'date': 0, 'dim': 'months_extracted', 'regex': re.compile(r'in (eine|einer|einem|einen|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) monat')},
        {'date': 2, 'dim': 'years', 'regex': re.compile(u'(uebernaechste|übernächste)[smn]{0,1} jahr')},
        {'date': 1, 'dim': 'years', 'regex': re.compile(u'(nächste|naechste)[snm]{0,1} jahr')},
        {'date': 0, 'dim': 'years_extracted', 'regex': re.compile(r'in ([\d]+) jahr')},
        {'date': 0, 'dim': 'years_extracted', 'regex': re.compile(r'in (eine|einer|einem|einen|ein|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn) jahr')} ]


phone_detector = re.compile(r'^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}$')


class MLDateTimePhoneDetector:
    PIT = 'PIT'
    PIT_NOW = 'PIT_NOW'
    PIT_NOW_SPECIAL = 'PIT_NOW_SPECIAL'
    TIME_FRAME = 'TIME_FRAME'
    PHONE = 'PHONE'
    PIT_PAST = 'PIT_PAST'
    PIT_FUTURE = 'PIT_FUTURE'

    def _detectTodayInQuery(self, originalQuery):
        thisQuery = originalQuery.lower()
        result = []
        # Let's first try the "today noon", "today afternoon", etc...
        for regex_comp in pit_detectors_now_special:
            regex = regex_comp['regex']
            code_to_exec = regex_comp['code'] # This is the lambda to call to get the special 'today' date...
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                sStart = match.span()[0]
                sEnd = match.span()[1]
                entry = thisQuery[sStart:sEnd]
                converted_time = code_to_exec(entry)
                result.append({'location': match.span(), 'found': entry, 'type': self.PIT_NOW_SPECIAL, 'converted': converted_time})

        for regex in pit_detectors_now:
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                alreadyFoundAsSpecialToday = False
                sStart = match.span()[0]
                sEnd = match.span()[1]
                for r in result:
                    if sStart == r['location'][0]:
                        alreadyFoundAsSpecialToday = True
                        break

                if not alreadyFoundAsSpecialToday:
                    entry = thisQuery[sStart:sEnd]
                    result.append({'location': match.span(), 'found': entry, 'type': self.PIT_NOW, 'converted': datetime.now().strftime('%Y-%m-%d %H:%M')})

        if len(result):
            return result
        else:
            return None



    def _convertFoundPITToDatetime(self, foundPIT, pitDetector):
        code_to_call = pitDetector['pre_code']
        result = code_to_call(foundPIT)
        dt = None
        try:
            dt = dtparser.parse(result)
        except:
            print('Could not convert ', result)
        if dt:
            return dt.strftime('%Y-%m-%d %H:%M')
        else:
            return foundPIT


    def _detectPITInQuery(self, originalQuery, resultsSoFar):
        thisQuery = originalQuery.lower()
        result = []
        for pitDetector in date_detectors:
            regex = pitDetector['regex']
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                sStart = match.span()[0]
                sEnd = match.span()[1]
                alreadyDetected = False
                foundPIT = thisQuery[sStart:sEnd]
                for r in result:
                    existingItemLoc = r['location']
                    if (sStart >= existingItemLoc[0] and sEnd <= existingItemLoc[1]) or (existingItemLoc[0] == sStart):
                        alreadyDetected = True
                        break

                if not alreadyDetected:
                    for prevResult in resultsSoFar:
                        existingItemLoc = prevResult['location']
                        if (sStart >= existingItemLoc[0] and sEnd <= existingItemLoc[1]) or (existingItemLoc[0] == sStart):
                            alreadyDetected = True
                            break

                if not alreadyDetected:
                    foundPIT = thisQuery[sStart:sEnd]
                    actualPIT = self._convertFoundPITToDatetime(foundPIT, pitDetector)
                    result.append({'location': match.span(), 'found': foundPIT, 'type': self.PIT, 'converted': actualPIT})
        if len(result):
            return result
        else:
            return None

    

    def _convertFoundTimeframeToDatetime(self, foundTimeframe):
        return foundTimeframe

    def _detectTimeframeInQuery(self, originalQuery):
        thisQuery = originalQuery.lower()
        result = []
        for regex in time_frame_detectors:
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                sStart = match.span()[0]
                sEnd = match.span()[1]
                foundTimeframe = thisQuery[sStart:sEnd]
                alreadyDetected = False
                for r in result:
                    if r['location'][0] == sStart:
                        alreadyDetected = True
                if not alreadyDetected:
                    actualTimeframe = self._convertFoundTimeframeToDatetime(foundTimeframe)
                    result.append({'location': match.span(), 'found': foundTimeframe, 'type': self.TIME_FRAME, 'converted': actualTimeframe})
        if len(result):
            return result
        else:
            return None



    def _convertFoundPhone(self, foundPhone):
        return foundPhone

    def _detectPhoneInQuery(self, originalQuery):
        thisQuery = originalQuery.lower()
        result = []
        iterator = phone_detector.finditer(thisQuery)
        for match in iterator:
            sStart = match.span()[0]
            sEnd = match.span()[1]
            foundPhone = thisQuery[sStart:sEnd]
            actualPhone = self._convertFoundPhone(foundPhone)
            result.append({'location': match.span(), 'found': foundPhone, 'type': self.PHONE, 'converted': actualPhone})
        if len(result):
            return result
        else:
            return None
        return None



    def _convertFoundPastFuturePIT(self, foundPIT, pitDetector):
        returnValue = None
        numValue = pitDetector['date']
        dimension = pitDetector['dim']
        if dimension == 'hours':
            td = timedelta(hours=numValue)
            returnValue = datetime.now() + td
        elif dimension == 'days':
            td = timedelta(days=numValue)
            returnValue = datetime.now() + td
        elif dimension == 'weeks':
            td = timedelta(weeks=numValue)
            returnValue = datetime.now() + td
        elif dimension == 'months':
            td = timedelta(days=31 * numValue)
            returnValue = datetime.now() + td
        elif dimension == 'years':
            td = timedelta(days=365 * numValue)
            returnValue = datetime.now() + td
        elif dimension == 'hours_extracted':
            print('TODO: HOURS_EXTRACTED)')
        elif dimension == 'days_extracted':
            print('TODO: DAYS_EXTRACTED')
        elif dimension == 'weeks_extracted': 
            print('TODO: WEEKS_EXTRACTED')
        elif dimension == 'months_extracted':
            print('TODO: MONTHS_EXTRACTED')
        elif dimension == 'years_extracted':
            print('TODO: YEARS_EXTRACTED')
        if returnValue:
            return returnValue.strftime('%Y-%m-%d %H:%M')

    def _detectPastFuturePITInQuery(self, originalQuery):
        thisQuery = originalQuery.lower()
        result = []

        for pitDetector in pit_detectors_past:
            regex = pitDetector['regex']
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                sStart = match.span()[0]
                sEnd = match.span()[1]
                foundPIT = thisQuery[sStart:sEnd]
                alreadyDetected = False
                for r in result:
                    existingItemLoc = r['location']
                    if (sStart >= existingItemLoc[0] and sEnd <= existingItemLoc[1]) or (existingItemLoc[0] == sStart):
                        alreadyDetected = True
                        break

                if not alreadyDetected:
                    actualPIT = self._convertFoundPastFuturePIT(foundPIT, pitDetector)
                    result.append({'location': match.span(), 'found': foundPIT, 'type': self.PIT_PAST, 'converted': actualPIT})

        for pitDetector in pit_detectors_future:
            regex = pitDetector['regex']
            iterator = regex.finditer(thisQuery)
            for match in iterator:
                sStart = match.span()[0]
                sEnd = match.span()[1]
                foundPIT = thisQuery[sStart:sEnd]
                alreadyDetected = False
                for r in result:
                    existingItemLoc = r['location']
                    if (sStart >= existingItemLoc[0] and sEnd <= existingItemLoc[1]) or (existingItemLoc[0] == sStart):
                        alreadyDetected = True
                        break
                if not alreadyDetected:
                    actualPIT = self._convertFoundPastFuturePIT(foundPIT, pitDetector)
                    result.append({'location': match.span(), 'found': foundPIT, 'type': self.PIT_FUTURE, 'converted': actualPIT})

        if len(result):
            return result
        else:
            return None


    def detectDataInText(self, originalText):
        result = []
        bwr = self._detectTodayInQuery(originalText)
        if bwr:
            result.extend(bwr)

        bwr = self._detectTimeframeInQuery(originalText)
        if bwr:
            result.extend(bwr)

        bwr = self._detectPITInQuery(originalText, result)
        if bwr:
            result.extend(bwr)

        bwr = self._detectPhoneInQuery(originalText)
        if bwr:
            result.extend(bwr)

        bwr = self._detectPastFuturePITInQuery(originalText)
        if bwr:
           result.extend(bwr)

        if len(result):
            result = sorted(result, key=lambda item: item['location'][0])
            return result
        else:
            return None




class MLDateTimeEnricher:
    def __init__(self, configDictionary):
        self.dataDetector = MLDateTimePhoneDetector()

    def detectDataAndEnrichInText(self, originalText, doEnrich = False):
        resultArray = self.dataDetector.detectDataInText(originalText)
        returnString = originalText
        if doEnrich == True and resultArray:
            # Let's sort our found location result array in reverse order.
            # As we cannot add strings from the beginning (this would change all indexes), we need
            # to start from the end. We definitely want to change the string IN-PLACE
            resultArray = sorted(resultArray, key=lambda item: item['location'][0], reverse=True)
            for item in resultArray:
                sBegin = item['location'][0]
                sEnd = item['location'][1]
                returnString = returnString[:sEnd] + ' MLIsData=' + item['converted'] + ']' + returnString[sEnd:]
                if sBegin == 0:
                    returnString = '[' + returnString
                else:
                    returnString = returnString[:sBegin] + '[' + returnString[sBegin:]

        return returnString, resultArray



if __name__ == '__main__':
    enricher = MLDateTimeEnricher('Hello')
    lines = codecs.open('test.txt', 'r', 'utf-8').readlines()
    for line in lines:
        line = line.strip()
        resultString, resultArray = enricher.detectDataAndEnrichInText(line, True)
        print(line)
        print(resultString)
        # print(resultArray)
        print('*' * 80)

