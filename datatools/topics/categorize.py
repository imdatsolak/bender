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
from nltk.tokenize import word_tokenize, sent_tokenize

"""
Training Data Categorization - works in conjunction with topics
"""

punkt_remover = re.compile(r'[.,;:\'"/?!@#$%&*()\-_=+\[\]\{\}~`<>`]+')
file_list = []

def multi_sent_tokenize(text, return_as_single_array = False):
    global punkt_remover
    result = []
    if isinstance(text, list):
        aText = ''
        for row in text:
            aText += row + '\n'
    else:
        atext = text
    for sent in sent_tokenize(line):
        sent = punkt_remover.sub('', sent)
        if return_as_single_array:
            result.extend(word_tokenize(sent))
        else:
            result.append(word_tokenize(sent))

    return result


def simple_tokenize(line):
    line = punkt_remover.sub('', line)
    return word_tokenize(line)


def read_documents(top_directory, tokens_only = False, remove_stop_words=True, stop_words=None):
    global file_list
    print('Reading source data... ', end='')
    sys.stdout.flush()
    if remove_stop_words and not stop_words:
        stop_words = get_stop_words('en')
    for root, dirs, files in os.walk(top_directory):
        counter = 0
        files.sort()
        for filename in filter(lambda filename: filename.endswith('.json'), files):
            counter += 1
            filename = os.path.join(root, filename)
            mail = json.load(codecs.open(filename, 'r', 'utf-8'))
            fContents = mail['body']
            token_list = []
            for line in fContents:
                line = line.strip().lower()
                tokens = []
                for sent in sent_tokenize(line):
                    sent = punkt_remover.sub('', sent)
                    tokens.extend(word_tokenize(sent))
                if remove_stop_words is True:
                    stopped_tokens = [i for i in tokens if not i in stop_words]
                else:
                    stopped_tokens = tokens
                stopped_tokens = [token.lower().strip() for token in stopped_tokens if len(token)>1]
                token_list.extend(stopped_tokens)
            file_list.append(filename)
            if tokens_only:
                yield token_list
            else:
                yield gensim.models.doc2vec.TaggedDocument(token_list, [counter])
    print('done')



def analyze_directory(indir, jsonFile, outdir, threads=4):
    topics = json.load(codecs.open(jsonFile, 'r', 'utf-8'))
    doc2vecFile = os.path.join(outdir, 'doc2vec.emb')
    train_corpus = list(read_documents(indir, False, None))
    if os.path.exists(doc2vecFile):
        model = gensim.models.Doc2Vec.load(doc2vecFile)
    else:
        print('No Doc2Vec File yet, generating...')
        model = gensim.models.doc2vec.Doc2Vec(size=500, min_count=2, iter=20)
        model.build_vocab(train_corpus)
        model.train(train_corpus, total_examples=model.corpus_count, epochs=model.iter)
        model.save(doc2vecFile)
    # Now, let's infer our test-corpus
    for topic in topics.keys():
        tokens = topics[topic]
        inferred_vector = model.infer_vector(tokens)
        sims = model.docvecs.most_similar([inferred_vector], topn=len(model.docvecs))
        print('='*100)
        print('Test Document ({}): «{}»\n'.format(topic, ' '.join(tokens)))
	print(u'SIMILAR/DISSIMILAR DOCS PER MODEL %s:\n' % model)
	for label, index in [('MOST', 0), ('MEDIAN', len(sims)//2), ('LEAST', len(sims) - 1)]:
	    print(u'%s %s: «%s»\n' % (label, sims[index], ' '.join(train_corpus[sims[index][0]].words)), file_list[sims[index][0]])



def usage():
    print('Usage:')
    print('\tpython categorize.py -i|--indir <in-directory> -j|--json <jsonFile>')
    print()
    print('\t\t-i <in-directory>: contains files ending in .eml to convert')

    sys.exit(2)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'i:j:o:T', ['indir=', 'jsonFile=', 'outdir=','threads='])
    except getopt.GetoptError:
        usage()

    indir = None
    jsonFile = None
    outdir = None
    threads = 4
    for opt, arg in options:
        if opt in ('-i', '--indir'):
            indir = arg 
        elif opt in ('-o', '--outdir'):
            outdir = arg 
        elif opt in ('-j', '--json'):
            jsonFile = arg
        elif opt in ('-T', '--threads'):
            threads = int(arg)

    if indir is None or jsonFile is None or outdir is None:
        usage()

    logger = logging.getLogger(os.path.basename(sys.argv[0]))
    logging.basicConfig(filename='logfile.log', format='%(asctime)s: %(levelname)s: %(message)s')
    logging.root.setLevel(level=logging.INFO)
    logger.info('**************** NEW TRAINING SESSION STARTED: %s' % ' '.join(sys.argv))
    analyze_directory(indir, jsonFile, outdir, threads=threads)

