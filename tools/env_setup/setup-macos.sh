#!/bin/bash
if [[ $(id -u) -ne 0  ]]; then printf "ERROR:\n"; printf "\tThis script must be run as root-user (sudo...)\n"; printf "\tExiting!\n"; exit 1; fi

echo Bender for macOS =============================================
echo NOTE: Running Bender on MacOS is only possible in development
echo       mode. Production mode is not support!!!!
echo =============================================================
printf "\n"
[ ! -d /usr/share/nltk_download ] && echo "NLTK Directory Exists" || mkdir /usr/share/nltk_download
status=$?
if [[ $status -ne 0 ]]; then
    echo "Please switch off System Integrity Protection on your MacOS"
    echo "In order to do so, you have too boot into RECOVERY-Mode "
    echo "by rebooting you Mac and holding down CMD-R while booting."
    echo "Then start Terminal.app there and enter 'csrutil disable'. "
    echo "After that, please reboot your machine again..."
    exit 1
fi

[ -f /usr/local/bin/brew ] && echo "Homebrew already installed. Good Job" || /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
python get-pip-macos.py 
pip install --upgrade pip
pip install CyHunspell
pip install pandas
pip install --upgrade matplotlib
pip install scipy
pip install pyyaml
pip install nltk
python nltkdownload.py 
pip install -U spacy
python -m spacy download de
pip install pyenchant
pip install flask flask-restful pymongo requests gensim stop_words pandas sklearn pyemd annoy six
pip install wikipedia
printf "\n"
echo ====================================================================================
echo You are all set up. Have fun.
echo ====================================================================================

