# notebooks-translation-to-es

# Description

Here are the tools to begin a robust Jupyter notebook translation from English to Spanish

### translate2.py

Python script that basically calls the Google Translate API and applies it cell by
cell to a Jupyter notebook.
Also treats special cases like the Disclaimer and Attribution cells, text after a #
and after it finds 'label' inside code cells.

Usage:
python translate2.py notebook_in_english.ipynb -o notebook_en_espanol.ipynb

### changes.vi

Vi script to change common mistranslation, words we prefer untranslated or in a 
different way from what Google Translate do them and lines of characters that are
usually mishandled by Google Translate.
