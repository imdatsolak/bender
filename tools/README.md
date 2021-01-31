# Training Data Tools
This directory contains tools for converting to and from training data:

# 1. csv2train
This converts csv-files to training-format for Bender.

It is required that the CSV-file columns are separated by ';' (semicolon). The CSV-files *must* be in UTF-8, otherwise we can't process them.

The column-structure of the CSV-file is:

    qCategory;qType;Questio;Answer;a-m1-c1-ug1;a-m1-c1-ug2;...

The tool will create three files: traindata.pickle, traindata.json, traindata.txt

## traindata.json
This is for you only to see the structure and see that everything is fine. This is *not* used in Bender-training.

## traindata.txt
This is the file that you should put in your Bender-dictionary source file. It contains all the texts from the CSV-file as a large plain-text file.

## traindata.pickle
This is the actual training-file. You will need to point your configuration to this file.

## Usage
It is easy to use csv2train:

    python csv2train.py -i <input-csv-file> -o <output-dir>


# 2. mail2train
This is the tool that converts mail-based data to training data.

In this case, each question is in a file either in JSON-format or plain-text format.

The directory structure of the mail-source data is as such:

    <QUESTIONS>
        +- <category_name1>
        |   +- <mail-file1>.[txt | json]
        |   +- <mail-file2>.[txt | json]
        |   ...
        +- <category_name2>
        |   +- <mail-fileX>.[txt | json]
        |   +- <mail-fileY>.[txt | json]
        ...

The ANSWERS-directory structure is similar, except there should be only *one* file per category and the file needs to be TXT-file in UTF-8:

    <ANSWERS>
        +- <category_name1>
        |   +- <answer-file.txt>
        +- <category_name2>
        |   +- <answer-file.txt>
        ...

The output will again be a traindata.pickle, traindata.json and traindata.txt like with csv2train.py

## Usage
You use mail2train very easily:
    
    python mail2train.py -i <questions-dir> -a <answers-dir> -o <output-dir> [-t]

If you use the *-t* option, it means that the QUESTION-files are in plain-text format. If they are in JSON-format, you usually save them as:

    Array containg ONE dictionary per email. The dictionary KEYS are 'subject' and 'body'


# 3. brain2train
You use this tool to convert Brain-data to training format. The output will be, as usual, traindata.pickle, traindata.json and traindata.txt

## Usage
Easy to use:

    python brain2train.py -b <brain-pickle-file> -t <trainfile-name>

the '.pickle', '.json' and '.txt' will be appended to the trainfile-name

# 4. loganalyzer
This is the tool that you use to analyze log-files, namely *performance.log* and *requests.log*

It will tell you either that 'All Ok', meaning that the log is correct and complete *or* tell you in which line(s) the log was incorrect. It will first analyze the requests.log and if that one contains errors, it won't analyze the performance.log at all.

## Usage
    
    analyze_logs.py -r <requests-file> -p <performance-file> -s <public-secret>

The *public-secret* is the *log_hash* from the configuration file for the customer in question

