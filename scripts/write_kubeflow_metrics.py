# Copyright 2020 The Board of Trustees of the Leland Stanford Junior University
#
# Author: Jim Deng <Jim.deng@gmail.com>
#         Mehrad Moradshahi <mehrad@cs.stanford.edu>
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
import json


def write_ui_metadata_dlg(dialogue_filepath, nlu_filepath):
	metadata = {"outputs": [
		{
			"storage": "inline",
			"source": open(dialogue_filepath, 'r').read(),
			"format": 'csv',
			"type": "table",
			"header": ["set", "# dlgs", "# turns",
					   "complete dlgs exact match", "complete dlgs slot only",
					   "first turns exact match", "first turns slot only",
					   "turn by turn exact match", "turn by turn slot only",
					   "up to error exact match", "up to error slot only",
					   "time to first error exact match", "time to first error slot only"
					   ]
		},
		{
			"storage": "inline",
			"source": open(nlu_filepath, 'r').read(),
			"format": 'csv',
			"type": "table",
			"header": ["Eval Set", "Device", "Turn Number", "# turns", "Accuracy", "w/o params", "Function", "Device",
					   "Num Function", "Syntax"]
		},
	]}
	with open('/tmp/mlpipeline-ui-metadata.json', 'w') as fout:
		json.dump(metadata, fout)


def write_ui_metadata(nlu_filepath):
	metadata = {"outputs": [
		{
			"storage": "inline",
			"source": open(nlu_filepath, 'r').read(),
			"format": 'csv',
			"type": "table",
			"header": ["Eval Set", "Domain", "Dataset size", "Accuracy", "w/o params", "Function", "Device", "Num Function", "Syntax"]
		},
	]}
	with open('/tmp/mlpipeline-ui-metadata.json', 'w') as fout:
		json.dump(metadata, fout)



def write_metrics_dlg(dialogue_filepath):
	with open(dialogue_filepath, 'r') as fin:
		line = fin.readlines()[0]
		parts = list(map(lambda p: p.strip(), line.split(',')))
		first_turn, turn_by_turn = parts[5], parts[7]
	metrics = {
		'metrics': [
			{'name': 'first-turn-em', 'numberValue': first_turn, 'format': "PERCENTAGE"},
			{'name': 'turn-by-turn-em', 'numberValue': turn_by_turn, 'format': "PERCENTAGE"},
		]
	}
	with open('/tmp/mlpipeline-metrics.json', 'w') as fout:
		json.dump(metrics, fout)

def write_metrics(nlu_filepath):
	with open(nlu_filepath, 'r') as fin:
		line = fin.readlines()[0]
		parts = list(map(lambda p: p.strip(), line.split(',')))
		exact_match, structure_match = parts[3], parts[4]
	metrics = {
		'metrics': [
			{'name': 'em', 'numberValue': exact_match, 'format': "PERCENTAGE"},
			{'name': 'sm', 'numberValue': structure_match, 'format': "PERCENTAGE"},
		]
	}
	with open('/tmp/mlpipeline-metrics.json', 'w') as fout:
		json.dump(metrics, fout)

if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	
	parser.add_argument('--dialogue_results', type=str)
	parser.add_argument('--nlu_results', type=str)
	parser.add_argument('--id_dlg', action='store_true')
	
	args = parser.parse_args()
	
	if args.id_dlg:
		write_ui_metadata_dlg(args.dialogue_results, args.nlu_results)
		write_metrics_dlg(args.dialogue_results)
	else:
		write_ui_metadata(args.nlu_results)
		write_metrics(args.nlu_results)
	
