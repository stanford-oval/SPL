import csv
from argparse import ArgumentParser
import os
from collections import defaultdict

parser = ArgumentParser()

parser.add_argument('--input_folder', type=str)
parser.add_argument('--output_csv_file', type=str)
parser.add_argument('--split', default='eval', type=str)
parser.add_argument('--column', default=1, type=int)
parser.add_argument('--all_languages', nargs='+')
parser.add_argument('--read_from', nargs='+', default=['final-qpis', 'final-qpis-no-glossary', 'final-qpis-no-glossary-op'])

args = parser.parse_args()

fieldnames = [lang + '_' + basename for lang in args.all_languages for basename in args.read_from]


all_data = defaultdict(list)
for folder in os.listdir(args.input_folder):
    if folder not in args.all_languages:
        continue
    for subfolder in os.listdir(os.path.join(args.input_folder, folder)):
        if subfolder not in args.read_from:
            continue
        fieldname = folder + '_' + subfolder
        with open(os.path.join(*[args.input_folder, folder, subfolder, args.split + '.tsv']), 'r') as f_in:
            for line in f_in:
                parts = list(map(lambda part: part.strip(), line.split('\t')))
                all_data[fieldname].append(parts[args.column])
                

assert len(set([len(values) for values in all_data.values()])) == 1

all_keys = all_data.keys()
len_values = len(list(all_data.values())[0])

with open(args.output_csv_file, 'w') as f_out:
    csv_writer = csv.DictWriter(f_out, fieldnames)
    csv_writer.writeheader()
    
    for index in range(len_values):
        row = dict()
        for key in all_keys:
            row[key] = all_data[key][index]
        csv_writer.writerow(row)

                
        
        
        
        





