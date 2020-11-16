#!/usr/bin/python3

import sys
import json
import re

quoted_pattern_maybe_space = re.compile(r'\"\s?([^"]*?)\s?\"')

with open(sys.argv[1]) as fin:
    data = fin.read().splitlines()

with open(sys.argv[2]) as fin:
    vocab_dict = json.load(fin)
value_set = vocab_dict['value_set']
all_values = {}
for domain, slot_dict in value_set.items():
    for dict in slot_dict.values():
        all_values.update(dict)
    



def find_translation(param):
    if param in all_values.keys():
        return all_values[param]
    else:
        #TODO improve
        return param


def main():
    with open(sys.argv[3], 'w') as fout:
        for line in data:
            _id, context, sentence, program = tuple(map(lambda text: text.strip(), line.strip().split('\t')))
            
            all_params = quoted_pattern_maybe_space.findall(program)
            
            param_map = {}
            
            for param in all_params:
                trans_param = find_translation(param)
                param_map[0] = trans_param
    
    
            prog_matches = list(re.finditer(quoted_pattern_maybe_space, program))
    
            # move through characters
            tokens = []
            curr = 0
            for pos, match in enumerate(prog_matches):
                start, end = match.span()
                if start > curr:
                    tokens.append(program[curr:start])
                tokens.append('" ' + param_map[0] + ' "')
                curr = end
            if curr < len(program):
                tokens.append(program[curr:])
    
            new_program = ' '.join(tokens)

            fout.write('\t'.join([_id, context, sentence, new_program]) + '\n')
        

main()
