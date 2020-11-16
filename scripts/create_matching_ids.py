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


import os
import argparse
from tqdm import tqdm
from collections import defaultdict
import shutil
import re

parser = argparse.ArgumentParser()

parser.add_argument('--input_file', type=str, help='input file to read from')
parser.add_argument('--ref_file', type=str, help='reference file to match ids with')
parser.add_argument('-n', '--num_lines', default=-1, type=int,
                    help='maximum number of lines to translate (-1 to translate all)')
parser.add_argument('--new_input_file', type=str, help='new input file')
parser.add_argument('--new_ref_file', type=str, help='new reference file')

args = parser.parse_args()

id_regex = re.compile('^[A-Z]+(\d+)[-\d]*?-(\d+)$')


def get_parts(line):
    _id, sent, prog = tuple(map(lambda text: text.strip(), line.strip().split('\t')))
    return _id, sent, prog

def process_id(_id):
    matches = id_regex.match(_id)
    processed_id = '-'.join(matches.groups())
    return processed_id

if __name__ == '__main__':
    
    ref_ids = []
    input_ids = []
    
    with open(args.input_file, 'r') as f_input:
        for line in tqdm(f_input):
            _id, _, _ = get_parts(line)
            input_ids.append(process_id(_id))

    with open(args.ref_file, 'r') as f_ref:
        for line in tqdm(f_ref):
            _id, _, _ = get_parts(line)
            ref_ids.append(process_id(_id))

            
    # first make sure ids for each file are uniq
    assert len(set(input_ids)) == len(input_ids)
    assert len(set(ref_ids)) == len(ref_ids)
    
    read_input_indices = []
    read_ref_indices = []
    
    # find matching sentence ids in input and ref files
    for i, _id in tqdm(enumerate(ref_ids)):
        try:
            _id_index = input_ids.index(_id)
            read_ref_indices.append(i)
            read_input_indices.append(_id_index)
        except:
            print('could not find a sentence with matching id in input file for id: {}'.format(_id_index))
            
     
    # write to new ref file
    with open(args.ref_file, 'r') as f_in, open(args.new_ref_file, 'w') as f_out:
        for i, line in enumerate(f_in):
            if i in read_ref_indices:
                f_out.write(line)
                
    # write to new input file
    with open(args.input_file, 'r') as f_in, open(args.new_input_file, 'w') as f_out:
        for i, line in enumerate(f_in):
            if i in read_input_indices:
                f_out.write(line)
