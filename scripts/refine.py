# Copyright 2020 The Board of Trustees of the Leland Stanford Junior University
#
# Author: Mehrad Moradshahi <mehrad@cs.stanford.edu>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#  list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#  this list of conditions and the following disclaimer in the documentation
#  and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#  contributors may be used to endorse or promote products derived from
#  this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import argparse
import sys
import re

sys.path.append('../')
from multilanguage.scripts.re_patterns import *


parser = argparse.ArgumentParser()

parser.add_argument('--input_file', type=str, help='input file to read from')
parser.add_argument('--orig_input_file', type=str, help='input file to read from')
parser.add_argument('--output_file', type=str, help='output file to write translations to')
parser.add_argument('-n', '--num_lines', default=-1, type=int, help='maximum number of lines to translate (-1 to translate all)')
parser.add_argument('-sl', '--sentence_lang', default='en', type=str, help='sentence language')
parser.add_argument('--silent', action='store_true', help='Do not pint outputs to stdout (only effective when output_file is provided)')
parser.add_argument('--refine_method', type=str, default='quoted_mapping', choices=['quoted_mapping', 'position_in_program'], help='find parameters based on this choice')


args = parser.parse_args()
language = args.sentence_lang



def get_parts(line):
    return tuple(map(lambda text: text.strip(), line.strip().split('\t')))

def find_mapping(sent, prog, match_pattern, key):
    

    mapping = dict()
    sent_matches = list(map(lambda match: match.group(1), re.finditer(match_pattern, sent)))
    prog_matches = list(map(lambda match: match.group(1), re.finditer(match_pattern, prog)))

    assert len(sent_matches) == len(prog_matches)
    
    if key == 'program':
        for pos, tokens in enumerate(prog_matches):
            mapping[pos] = sent_matches.index(tokens)
    elif key == 'sentence':
        for pos, tokens in enumerate(sent_matches):
            mapping[pos] = prog_matches.index(tokens)
    return mapping


def quoted_mapping(orig_line, line):
    
    _id, sent, prog = get_parts(line)
    orig_id, orig_sent, orig_prog = get_parts(orig_line)
    
    _id_number = re.search(id_number_pattern, _id).group()
    orig_id_number = re.search(id_number_pattern, orig_id).group()

    assert _id_number == orig_id_number
    
    match_pattern = entity_pattern
    mapping = find_mapping(orig_sent, orig_prog, match_pattern, 'program')

    # preprocess input sentence
    # we assume input is always unquoted
    
    # match strings
    input_example_pattern = quoted_pattern_maybe_space_or_number
    sent_matches = list(re.finditer(input_example_pattern, sent))
    prog_matches = list(re.finditer(input_example_pattern, prog))
    
    
    sent_params = []
    for match in sent_matches:
        # number
        if match.group(2) is not None:
            sent_params.append((match, 'number'))
        # string
        else:
            sent_params.append((match, 'string'))
   
    prog_params = []
    for match in prog_matches:
        # number
        if match.group(2) is not None:
            prog_params.append((match, 'number'))
        # string
        else:
            prog_params.append((match, 'string'))
    
    # if original quoted dataset have actual numbers which are not requoted drop them
    if len(mapping) < len(sent_matches):
        # find unquoted numbers in original sentence
        orig_sent_numbers = list(map(lambda match: match.group(1), re.finditer(number_pattern, orig_sent)))
        
        # drop those values from the sentence and program parameters
        new_sent_params = []
        new_prog_params = []
        for (match, type) in sent_params:
            if type == 'number' and match.group(2) in orig_sent_numbers:
                continue
            new_sent_params.append((match, type))
        for (match, type) in prog_params:
            if type == 'number' and match.group(2) in orig_sent_numbers:
                continue
            new_prog_params.append((match, type))
        # assign back new values
        sent_params = new_sent_params
        prog_params = new_prog_params
        
    # if the program has numbers which are not present in the sentence, drop them from prog_params
    if len(sent_matches) < len(prog_matches):
        
        sent_numbers = [match.group(2) for (match, type) in sent_params if type == 'number']
        
        new_prog_params = []
        for (match, type) in prog_params:
            if type == 'number' and match.group(2) not in sent_numbers:
                continue
            new_prog_params.append((match, type))
        # assign back new values
        prog_params = new_prog_params
        
    try:
        assert len(sent_params) == len(prog_params)
        assert len(sent_params) == len(mapping)
    except:
        print('**** here ****')
        print(line)
        print('** program and sentence does not have same number of parameters')
        print('sent_params: ', sent_params)
        print('prog_params: ', prog_params)
        print('original mapping', mapping)
        print('**************')
        raise ValueError
    
    tokens = []
    curr = 0
    for pos, (match, type) in enumerate(prog_params):
        start, end = match.span()
        if start > curr:
            tokens.append(prog[curr:start])
        replace_match = sent_params[mapping[pos]]
        try:
            assert replace_match[1] == type
        except:
            print('Sadly translated sentence and quoted sentence do not have matching param positions.')
            raise ValueError
        if type == 'number':
            tokens.append(replace_match[0].group(2))
        else:
            tokens.append('" ' + replace_match[0].group(1) + ' "')
        curr = end
    if curr < len(prog):
        tokens.append(prog[curr:])
        
    new_response = ''.join(tokens)

    return new_response


def position_in_program(orig_line, line):
    
    _id, sent, prog = get_parts(line)
    orig_id, orig_sent, orig_prog = get_parts(orig_line)
    
    _id_number = re.search(id_number_pattern, _id).group()
    orig_id_number = re.search(id_number_pattern, orig_id).group()

    assert _id_number == orig_id_number

    match_pattern = entity_pattern
    # drop DATE and DURATION before matching
    sent = ' '.join([token for token in sent.split(' ') if not (token.startswith('DATE') or token.startswith('DURATION'))])
    prog = ' '.join([token for token in prog.split(' ') if not (token.startswith('DATE') or token.startswith('DURATION'))])
    
    mapping = find_mapping(sent, prog, match_pattern, 'sentence')

    # preprocess input sentence
    # we assume input is always quoted and orig in always unquoted
    
    # match strings
    input_example_pattern = quoted_pattern_maybe_space_or_number
    orig_prog_matches = list(re.finditer(input_example_pattern, orig_prog))
    sent_matches = list(re.finditer(match_pattern, sent))
    prog_matches = list(re.finditer(match_pattern, prog))
    
    
    sent_numbers = [match.group(1) for match in list(re.finditer(number_pattern, orig_sent))]
    sent_matches_contain_number = any(match.group(1).startswith('NUMBER') for match in sent_matches)
    
    # if original program has numbers that have not been requoted drop them from orig_prog_matches
    if len(prog_matches) < len(orig_prog_matches):
        new_orig_prog_matches = []
        for match in orig_prog_matches:
            if match.group(2) is not None and (match.group(2) in sent_numbers or not sent_matches_contain_number):
                continue
            new_orig_prog_matches.append(match)
        orig_prog_matches = new_orig_prog_matches
    
    try:
        assert len(sent_matches) == len(prog_matches) == len(mapping)
        assert len(orig_prog_matches) == len(prog_matches)
    except:
        print('**** here ****')
        print(line)
        print('orig_prog_matches:', orig_prog_matches)
        print('sent_matches:', sent_matches)
        print('prog_matches:', prog_matches)
        print('mapping:', mapping)
        print('**************')
        raise ValueError
    
    new_sentence = []
    curr = 0
    for pos, match in enumerate(sent_matches):
        start, end = match.span()
        if start > curr:
            new_sentence.append(sent[curr:start])
        replace_match = orig_prog_matches[mapping[pos]]
        replace_match_val = replace_match.group(2) if replace_match.group(2) else replace_match.group(1)
        new_sentence.append('" ' + replace_match_val + ' "')
        curr = end
    if curr < len(sent):
        new_sentence.append(sent[curr:])
        
    new_response = ''.join(new_sentence)

    return new_response


if __name__ == '__main__':
    with open(args.input_file, 'r') as f_in, open(args.orig_input_file) as f_orig, open(args.output_file, 'w+') as f_out:
        lines = f_in.read().splitlines()
        orig_lines = f_orig.read().splitlines()
        if args.num_lines != -1:
            selected_lines = lines[:min(args.num_lines, len(lines))]
        else:
            selected_lines = lines
            
        need_fixing = 0
        
        refine_method = args.refine_method
    
        for orig_line, line in zip(orig_lines, selected_lines):
            try:
                _id, sent, prog = get_parts(line)
                orig_id, orig_sent, orig_prog = get_parts(orig_line)
                print('processing sentence with id:', _id)
                print(sent)
                if refine_method == 'quoted_mapping':
                    new_program = quoted_mapping(orig_line, line)
                    if not args.silent:
                        print('processing was successful for sentence with id:', _id)
                        print(prog + '  ------>  ' + new_program + '\n')
                    f_out.write('\t'.join([_id, sent, new_program]) + '\n')
                        
                elif refine_method == 'position_in_program':
                    new_sentence = position_in_program(orig_line, line)
                    if not args.silent:
                        print('processing was successful for sentence with id:', _id)
                        print(sent + '  ------>  ' + new_sentence + '\n')
                    f_out.write('\t'.join([_id, new_sentence, orig_prog]) + '\n')

                
            except:
                print('***Processing failed for example with id:***', _id)
                f_out.write(orig_line + '\n')
                need_fixing += 1
        
        print('{} out of {} examples could not be processed'.format(need_fixing, len(selected_lines)))

