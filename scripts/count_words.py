import argparse
import sys

parser = argparse.ArgumentParser()

parser.add_argument('--input_file', type=str, help='input file to read from')

args = parser.parse_args()

sys.path.append('../')
from SPL.scripts.re_patterns import *

counts = 0
with open(args.input_file, 'r') as f_input:
    for line in f_input:
        id_, sent, prog = map(lambda part: part.strip(), line.split('\t'))
        tokens = sent.split(' ')
        between_quotes = False
        for token in tokens:
            if token == '"':
                between_quotes = not between_quotes
                continue
            if between_quotes:
                continue
            if token == ' ' or token in punctuation_string or entity_pattern.findall(token):
                continue
            
            counts += 1

print('File has {} number of words'.format(counts))






