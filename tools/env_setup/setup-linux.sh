#!/bin/bash
apt-get update
apt-get upgrade -y
apt-get install git -y
apt-get install python2.7 -y
apt-get install python-pip -y
pip install --upgrade pip
apt-get install libblas-dev -y
apt-get install python-h5py -y
apt-get install libhunspell-dev -y
apt-get install hunspell -y
apt-get install enchant -y
pip install scipy
pip install pyyaml
pip install nltk
mkdir /usr/share/nltk_data
python nltkdownload.py < ./nltkd.txt
pip install -U spacy
python -m spacy download de
pip install pyenchant
pip install flask flask-restful pymongo requests gensim stop_words pandas sklearn pyemd annoy six hunspell
apt-get install apache2 -y
apt-get install libapache2-mod-wsgi
apt-get install apache2-dev -y
pip install mod_wsgi
pip install wikipedia
