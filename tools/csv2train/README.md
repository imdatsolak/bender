# csv2train

This directory contains the tool required to convert CSV-files into final training format.

This tool is used to convert CSV-Files into training-data format used by Bender.
Usage:
    csv2train.py -i <input-csv-file> -o <output-directory>

Created: 2017-06-08 09:00 CET, Imdat Solak

RULES:
    - The CSV-File *must* be semicolon (;)-delimited.
    - The CSV-file *must* be UTF-8
    - The first row *must* be the title row
    - The first answer-column *must* be the DEFAULT-ANSWER-COLUMN!!!
    - Column-titles allowed/understood:
        - Category
        - Type
        - Question
        - Answer
        - A-Mn-Cm-UGx (Answer for Client /n/ (M), Channel /m/, and UserGroup /x/)

NOTES: PLEASE READ THE README.md in this directory!!!
