# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import hashlib
import getopt
import codecs


"""
Log Analyzer
Created: 2017-12-04 08:00 CET, ISO
"""
class LogAnalyzer(object):
    def __init__(self, requests_log_file, performance_log_file, public_secret):
        self.key = 'nmxcvjkhsdf98u53429kjhasd901423jkhdsfzcxvmnuitgre4325809cneu3io'
        self.r_log =  requests_log_file
        self.p_log = performance_log_file
        hash_key = public_secret
        new_hash_key = self.key + hash_key
        self.hash_key = hashlib.sha256(new_hash_key).hexdigest()

    def analyze(self):
        r_log_has_errors = False
        p_log_has_errors = False
        r_log_entries = codecs.open(self.r_log, 'r', 'utf-8').readlines()
        prev_r_log_hash = self.hash_key
        for lineno, line in enumerate(r_log_entries):
            line = line.strip()
            result = line.split('\t')
            hash_key = result[-1]
            l_no_hash = result[:-1]
            l_str = '\t'.join(l_no_hash) + prev_r_log_hash
            line_hash = hashlib.md5(l_str).hexdigest()
            prev_r_log_hash = line_hash
            if line_hash != hash_key:
                r_log_has_errors = True
                print('REQUESTS-LOG: HASH-ERROR, line {}'.format(lineno))

        if not r_log_has_errors:
            p_log_entries = codecs.open(self.p_log, 'r', 'utf-8').readlines()
            prev_log_hash = self.hash_key
            for lineno, line in enumerate(p_log_entries):
                line = line.strip()
                perf_e = line.split('\t')
                p_hash = perf_e[-1]
                p_no_hash = perf_e[:-1]
                l_str = '\t'.join(p_no_hash)
                new_hash = hashlib.md5(l_str + prev_log_hash + self.hash_key).hexdigest()
                prev_log_hash = p_hash
                if new_hash != p_hash:
                    p_log_has_errors = True
                    print('PERFORMANCE-LOG: HASH-ERROR, line {}'.format(lineno))
                    print('\t[{}]\n\t[{}]'.format(line, l_str))
                else:
                    prev_log_hash = new_hash
        else:
            print('REQUESTS-LOG: There were errors in "requests.log". Cannot continue with performance.log analysis.')
        if not r_log_has_errors and not p_log_has_errors:
            print('LOGS ARE FINE!')


def main(requests_logf, performance_logf, public_secret):
    analyzer = LogAnalyzer(requests_logf, performance_logf, public_secret)
    analyzer.analyze()


try:
    options, arguments = getopt.getopt(sys.argv[1:], 'r:p:s:', ['requests', 'performance', 'secret'])
except getopt.GetoptError:
    help()
    sys.exit(1)

r_f = None
p_f = None
sec = None

for opt, arg in options:
    if opt in ('-r', '--requests'):
        r_f = arg
    elif opt in ('-p', '--performance'):
        p_f = arg
    elif opt in ('-s', '--secret'):
        sec = arg

if r_f is None or p_f is None or sec is None:
    print('Usage:\n\tanalyze_logs.py -r <requests-file> -p <performance-file> -s <public-secret>')
    sys.exit(1)
else:
    main(r_f, p_f, sec)

