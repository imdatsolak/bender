# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import sys 
reload(sys)
sys.setdefaultencoding("utf-8")
import os
import email
import re
import json
import gensim
import codecs
import getopt
import logging
import shutil
from nltk.tokenize import word_tokenize, sent_tokenize
from gensim.similarities import WmdSimilarity
from stop_words import get_stop_words
from multiprocessing import Lock, Process, Queue, current_process
from progressbar import ProgressBar, Percentage, Bar, ETA, FormatLabel, AnimatedMarker
from utils import multi_sent_tokenize, simple_tokenize
from hunspelling import HunSpelling
from enchantspelling import EnchantSpelling

"""
Training Data Categorization - works in conjunction with gen2wv

Copyright (c) 2019 Imdat Solak
All Rights Reserved.

Written: 2017-09-2x ??:?? CET, ISO

This tool tries to categorize the input data (raw data in JSON-Format) into the
categories described in the -j (JSON-Config-File).

This is the multi-process version as WMD takes quite some time to run.
"""

punkt_remover = re.compile(r'[.,;:\'"/?!@#$%&*()\-_=+\[\]\{\}~`<>`]+')
file_list = []


def perform_query_on_corpus(wmd_instance, validate_corpus, vc_index, total_vc_size, num_threads, in_q, out_q):
    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    sims_array = []
    sims = []
    num_docs = total_vc_size
    if vc_index == num_threads -1:
        widgets=[FormatLabel('Document: [%(value)s/'+str(num_docs)+']'), ' ', Percentage(), ' ', Bar(marker='@', left='[', right=']'), ' ', ETA()]

        pBar = ProgressBar(widgets=widgets, maxval=num_docs).start()

    for i, document in enumerate(validate_corpus):
        if vc_index == num_threads -1:
            n = i * num_threads
            if n>num_docs:
                n = num_docs
            pBar.update(n, '')
        if document is not None and len(document)>0:
            sims = wmd_instance[document]
            if sims:
                sims_array.append(sims)

    if vc_index == num_threads -1:
        pBar.finish()
        print('Please note: there may be still other multi-processes running. Please wait...', end='')
        sys.stdout.flush()
    out_q.put(vc_index)
    out_q.put(sims_array)
    out_q.close()
    done = in_q.get()
    os._exit(0)


def read_train_docs(top_directory, remove_stop_words=False, stop_words=None, speller=None, stemmer=None):
    print('Reading Training Documents... ', end='')
    sys.stdout.flush()
    topics = {}
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('de')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        for directory in dirs:
            topics[directory] = []
        for filename in filter(lambda filename: filename.endswith('.json'), files):
            counter += 1
            filename = os.path.join(root, filename)
            mail = json.load(codecs.open(filename, 'r', 'utf-8'))
            body = mail['body']
            body = unicode(body)
            title = mail.get('subject', '')
            title = unicode(title)
            fContents = []
            if title != '':
                fContents.append(title)
            fContents.extend(body)
            token_list = []
            mail_text = ' '.join(fContents)
            file_topic = os.path.basename(os.path.dirname(filename))
            if file_topic in topics.keys():
                topics[file_topic].append(mail_text)
    print('done')
    return topics


def read_documents(top_directory, tokens_only = False, remove_stop_words=False, stop_words=None, speller=None, stemmer=None):
    global file_list
    print('Reading validation documents... ', end='')
    sys.stdout.flush()
    result_list = []
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('de')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        files.sort()
        for filename in filter(lambda filename: filename.endswith('.json'), files):
            counter += 1
            filename = os.path.join(root, filename)
            mail = json.load(codecs.open(filename, 'r', 'utf-8'))
            body = mail['body']
            title = mail.get('subject', '')
            fContents = []
            if title != '':
                fContents.append(title)
            fContents.extend(body)
            token_list = []
            for line in fContents:
                line = line.strip().lower()
                tokens = simple_tokenize(line)

                if remove_stop_words is True:
                    stopped_tokens = [i for i in tokens if not i in stop_words]
                else:
                    stopped_tokens = tokens
                stopped_tokens = [token for token in stopped_tokens if len(token)>1]
                if speller != None:
                    stopped_tokens = speller.getSpellCheckedWordList(stopped_tokens)
                if stemmer != None:
                    stopped_tokens = stemmer.stemWordList(stopped_tokens)
                token_list.extend(stopped_tokens)
            file_list.append(filename)
            if tokens_only:
                result_list.append(token_list)
            else:
                result_list.append(gensim.models.doc2vec.TaggedDocument(token_list, [counter]))
    print('done')
    return result_list


def print_sim(document, sims, train_corpus, topic2docid):
    print('*' * 100)
    print(' '.join(document))
    for sim in sims:
        print('{:-.6f} --> {} --> {}'.format(sim[1], topic2docid[sim[0]], ' '.join(train_corpus[sim[0]])))


def generate_gt_wmd():
    return None

def analyze_directory(indir, ground_truth_dir, w2v_file, outfile, verbose, outdir, numthreads, lang, remove_stop_words, speller=None, stemmer=None):
    try:
        w2v_model = gensim.models.Word2Vec.load(w2v_file)
    except:
        print('Could not read W2V-File ({})'.format(w2v_file))
        sys.exit(1)

    stop_words = None
    if remove_stop_words:
        stop_words = get_stop_words(lang)

    topic2docid = []
    topics = read_train_docs(ground_truth_dir, remove_stop_words, stop_words, speller, stemmer)

    train_corpus = []
    for key in topics.keys():
        documents = topics[key]
        for document in documents:
            topic2docid.append(key)
            document_tokens = simple_tokenize(document)
            train_corpus.append(document_tokens)


    print('Generating WMD instances... ', end='')
    sys.stdout.flush()
    wmd_instances = []
    for i in range(numthreads):
        wmd_instance = WmdSimilarity(train_corpus, w2v_model, min(len(train_corpus), 3))
        wmd_instances.append(wmd_instance)

    print('done')
    validate_corpus = read_documents(indir, True, remove_stop_words, stop_words, speller, stemmer)
    chunk_size = int(len(validate_corpus) / numthreads)
    result_list = {}
    queues = []
    processes = []
    results = []
    for instance in range(numthreads):
        in_q = Queue()
        out_q = Queue()
        queues.append([in_q, out_q])
        if instance == numthreads -1:
            sp = Process(target=perform_query_on_corpus, args=(wmd_instances[instance], validate_corpus[instance * chunk_size:], instance, len(validate_corpus), numthreads, in_q, out_q))
        else:
            sp = Process(target=perform_query_on_corpus, args=(wmd_instances[instance], validate_corpus[instance * chunk_size: (instance+1) * chunk_size], instance, len(validate_corpus), numthreads, in_q, out_q))
        processes.append(sp)

    for sp in processes:
        sp.start()

    for i, sp in enumerate(processes):
        q = queues[i]
        in_q = q[0]
        out_q = q[1]
        vc_index = out_q.get()
        sims_array = out_q.get()
        in_q.put('THANKS')
        in_q.close()
        sp.join()
        if sims_array != None and len(sims_array)>0:
            res = []
            for l_docId, sims in enumerate(sims_array):
                docId = (vc_index * chunk_size)  + l_docId
                if verbose:
                    print_sim(validate_corpus[docId], sims, train_corpus, topic2docid)
                if sims:
                    result_list[file_list[docId]] = { 'sim': sims[0][1], 'type': topic2docid[sims[0][0]]}

    print('done analyzing.')
    if isinstance(outfile, basestring):
        json_out_f = codecs.open(outfile, 'w', 'utf-8')
    else:
        json_out_f = outfile
    print(json.dumps(result_list, indent=4), file=json_out_f)
    if isinstance(outfile, basestring):
        json_out_f.close()
    if outdir is not None:
        print('Copying files into subdirectories of {} ... '.format(outdir), end='')
        sys.stdout.flush()
        for key in topics.keys():
            if '/' in key:
                key = key.replace('/', '_')
            if ':' in key:
                key = key.replace(':', '_')
            path = os.path.join(outdir, key)
            if not os.path.exists(path):
                os.makedirs(path)

        for source_file in result_list.keys():
            dest_type = result_list[source_file]['type']
            dest_path = os.path.join(outdir, dest_type)
            dest_file = os.path.join(dest_path, os.path.basename(source_file))
            shutil.copyfile(source_file, dest_file)
        print('done')




def usage():
    print('Usage:')
    print('\tpython wmd_categorize.py -i|--indir <in-directory> -g|--gtruth <ground_truth_dir> -w|--w2v <word2vec-file> [-v] [-o|-outfile <outfile>] [-O|--outdir <dir-to-copy-files-to>] [--speller <hun|enchant>] [--stem] [--numthreads <n>]')
    print()
    print('\t-i <indir>         Directory containing .json-email-files')
    print('\t-g <gtruth_dir>    Directory containing `ground truth` mails. Each subdirectory represents a category!')
    print('\t-w <word2vec-file> The Word2Vec-file generated by gen2wv (just the .embeddings-file\'s name')
    print('\t-v                 Be verbose about your work')
    print('\t-o <outfile>       Write report into an outfile')
    print('\t-O <outdir>        Where to copy the .json-email-files to')
    print('\t--speller          The Spell-Checker to use (\'hun\' or \'enchant\'; default = no spelling)')
    print('\t--stem             Use stemming (hunspell\'s stemmer; default = no stemming)')
    print('\t--numthreads <n>   Use <n> threads to process (default=1)')
    sys.exit(1)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:w:vo:O:g:', ['indir=', 'w2v=', 'verbose', 'outfile=', 'outdir=', 'numthreads=', 'speller=', 'stem', 'gtruth='])
    except getopt.GetoptError:
        usage()

    hunspell_dict_file = 'resources/de_DE.dic'
    hunspell_aff_file = 'resources/de_DE.aff'
    tokenizer_language = 'german'
    language_short = 'de'
    language_long = 'de_DE'
    add_words_file = None
    remove_stop_words = False
    dictionary_dir = 'resources'

    indir = None
    outdir = None
    w2v_file = None
    verbose = False
    outfile = sys.stdout
    outdir = None
    numthreads = 1
    speller = None
    stemmer = None
    use_stemmer = False
    ground_truth_dir = None
    for opt, arg in options:
        if opt in ('-i', '--indir'):
            indir = arg 
        elif opt in ('-w', '--wmd'):
            w2v_file = arg
        elif opt in ('-v', '--verbose'):
            verbose = True
        elif opt in ('-o', '--outfile'):
            outfile = arg
        elif opt in ('-O', '--outdir'):
            outdir = arg
        elif opt == '--numthreads':
            numthreads = int(arg)
        elif opt == '--speller':
            speller_n = arg
            if speller_n == 'enchant':
                speller = EnchantSpelling(language_short, tokenizer_language, add_words_file)
            elif speller_n == 'hun':
                speller = HunSpelling(hunspell_dict_file, hunspell_aff_file, add_words_file, tokenizer_language, dictionary_dir, language_long)
            else:
                print('Unknow speller {}'.format(speller_n))
                usage()
        elif opt == '--stem':
            use_stemmer = True
        elif opt in ('-g', '--gtruth'):
            ground_truth_dir = arg


    if indir is None or ground_truth_dir is None or w2v_file is None:
        usage()

    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    if use_stemmer == True:
        if speller != None and isinstance(speller, HunSpelling):
            stemmer = speller
        else:
            stemmer = HunSpelling(hunspell_dict_file, hunspell_aff_file, add_words_file, tokenizer_language, dictionary_dir, language_long)

    if not os.path.exists('logs'):
        os.makedirs('logs')
    logging.basicConfig(filename='logs/logfile.log', format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info('**************** NEW TRAINING SESSION STARTED: %s' % ' '.join(sys.argv))
    analyze_directory(indir, ground_truth_dir, w2v_file, outfile, verbose, outdir, numthreads, language_short, remove_stop_words, speller=speller, stemmer=stemmer)

