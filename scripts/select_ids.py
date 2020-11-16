from argparse import ArgumentParser
import os

parser = ArgumentParser()

parser.add_argument('--input_file', default='./hotels/en/quoted/eval.tsv', type=str)
parser.add_argument('--ids_list_file', default='./data_factory/A_raw_file.txt',  type=str)
parser.add_argument('--output_file', default='./data_factory/select_ids_results', type=str)

args = parser.parse_args()

all_ids = []
with open(args.ids_list_file) as id_in:
    for id_ in id_in:
        id_ = id_.strip()
        if id_[0] == 'R':
            id_ = id_[1:]
        if id_.endswith('-0'):
            id_ = id_[:-2]
        all_ids.append(id_)

with open(args.input_file, 'r') as f_in, open(args.output_file, 'w') as f_out:
    for line in f_in:
        _id, sent, prog = tuple(map(lambda text: text.strip(), line.strip().split('\t')))
        if _id in all_ids:
            f_out.write(','.join([_id, sent]) + '\n')

            
        




