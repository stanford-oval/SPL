import csv
from argparse import ArgumentParser
import re

parser = ArgumentParser()

parser.add_argument('--input_file', type=str)
parser.add_argument('--output_csv_file', type=str)
parser.add_argument('--option', default='eval', choices=['eval', 'debug'])

args = parser.parse_args()

lang_regex = re.compile('lang=(\w+)')


row_dicts = []
with open(args.input_file, 'r') as f_in:
    for line in f_in:
    
        if args.option == 'eval':
            fieldnames = ['language', 'em_accuracy', 'bleu_score']
            em_regex = re.compile('\"em\":\s(\d+\.\d+)')
            bleu_regex = re.compile('"bleu":\s(\d+\.\d+)')
            
            if ('lang' in line):
                language = lang_regex.findall(line)[0]
            elif ('em' in line) or ('bleu' in line):
                em = em_regex.findall(line)[0]
                bleu = bleu_regex.findall(line)[0]
                
                row_dicts.append({'language': language, 'em_accuracy': em, 'bleu_score': bleu})
        
        elif args.option == 'debug':
            fieldnames = ['language', 'size', 'em_accuracy', 'em_wo_params', 'syntax']
    
            if ('lang' in line):
                language = lang_regex.findall(line)[0]
            elif 'eval' in line or 'test' in line:
                _, _, size, em, em_wo_params, fm, dm, nfm, syntax = map(lambda part: part.strip(), line.split(','))
                
                row_dicts.append({'language': language, 'size': size, 'em_accuracy': float(em)*100, 'em_wo_params': float(em_wo_params)*100, 'syntax': float(syntax)*100})

with open(args.output_csv_file, 'w') as f_out:
    csv_writer = csv.DictWriter(f_out, fieldnames)
    csv_writer.writeheader()
    
    csv_writer.writerows(row_dicts)











