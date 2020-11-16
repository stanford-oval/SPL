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
import re
from tqdm import tqdm
from collections import defaultdict
import numpy as np
import sys
import unicodedata

sys.path.append('../')
from re_patterns import *


cjk_chars = re.compile('[u30A0-\u30FF|\u3041-\u3096|\u3400-\u4DB5|\u4E00-\u9FCB|\uF900-\uFA6A|'
                       'あ|い|う|え|お|o|か|き|く|け|こ|が|ぎ|ぐ|げ|ご|さ|し|す|せ|そ|ざ|じ|ず|ぜ|ぞ|た|ち|つ|て|と|だ|ぢ|づ|で|ど|な|に|ぬ|ね|の|は|ひ|ふ|へ|ほ|ば|び|ぶ|べ|ぼ|ぱ|ぴ|ぷ|ぺ|ぽ|ま|み|む|め|も|や|ゆ|よ|ら|り|る|れ|ろ|わ|を|ん|'
                       '\u3000-\u303f|\u3040-\u309f|\u30a0-\u30ff|\uff00-\uffef0-9|\u4e00-\u9faf|\u4e00-\u9fff|\u31C0-\u31EF|\u3300-\u33FF0-9|\u4e00-\u9fff|\u31C0-\u31EF|\u3300-\u33FF]')



ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
]


def is_cjk(char):
  return any([range["from"] <= ord(char) <= range["to"] for range in ranges]) or char == '、'


parser = argparse.ArgumentParser()

parser.add_argument('--input_file', type=str, help='input file to read from')
parser.add_argument('--ref_file', type=str, help='reference file to read from; used to read ids from')
parser.add_argument('--output_file', type=str, help='output file to write translations to')
parser.add_argument('-n', '--num_lines', default=-1, type=int, help='maximum number of lines to translate (-1 to translate all)')
parser.add_argument('--input_delimiter', default='\t', type=str, help='delimiter used to split input files')
parser.add_argument('--remove_qpis', action='store_true', help='')
parser.add_argument('--prepare_for_gt', action='store_true', help='')
parser.add_argument('--prepare_for_marian', action='store_true', help='')
parser.add_argument('--post_process_translation', action='store_true', help='')
parser.add_argument('--match_ids', action='store_true', help='')
parser.add_argument('--remove_duplicate_sents', action='store_true', help='')
parser.add_argument('--reduce_duplicate_progs', action='store_true', help='')
parser.add_argument('--sents_to_keep', type=int, default=1, help='')
parser.add_argument('--add_token', default='T', help='prepend ids with this token after matching ids')
parser.add_argument('--replace_ids', action='store_true', help='replace dataset ids with sequential unique values')
parser.add_argument('--remove_qpip_numbers', action='store_true',
                    help='remove quotation marks around numbers in program')
parser.add_argument('--insert_space_quotes', action='store_true',
                    help='insert space between quotation marks and parameters if removed during translation')
parser.add_argument('--refine_sentence', action='store_true', help='')
parser.add_argument('--arabic2english_digits', action='store_true', help='')
parser.add_argument('--fix_punctuation', action='store_true', help='')
parser.add_argument('-sl', '--sentence_language', default='en')
parser.add_argument('--param_language', default='en')
parser.add_argument('--num_columns', type=int, default=3, help='number of columns in input file')
parser.add_argument('--process_oht', action='store_true', help='')
parser.add_argument('--compute_complexity', action='store_true', help='')
parser.add_argument('--remove_qspace', action='store_true', help='')
parser.add_argument('--preprocess_paraphrased', action='store_true', help='')
parser.add_argument('--no_lower_case', action='store_true', help='do not lower case tokens')
parser.add_argument('--no_unicode_normalize', action='store_true', help='do not unicode normalize examples')
parser.add_argument('--remove_spaces_cjk', action='store_true', help='')
parser.add_argument('--fix_spaces_cjk', action='store_true', help='')

args = parser.parse_args()

Ar2En_digit_map = {'۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'}

def capitalize(match):
    if isinstance(match, str):
        word = match
    else:
        word = match.group(0)
    return word[0].upper() + word[1:].lower()

def upper(match):
    word = match.group(0)
    return word.upper()

def backward_entity_mapping(entity):
    if entity.startswith('GENERIC_ENTITY'):
        
        try:
            base, name = entity.rsplit(':', 1)
            
            base = base.lower()
            base = re.sub(r'restaurant', capitalize, base)
            base = re.sub(r'hotel', capitalize, base)
    
            base = re.sub(r'generic_entity', upper, base)
            
            name = capitalize(name)
            
            if name.startswith('Us_state'):
                name = name.lower()
            
            if name.startswith('Locationfeaturespecification'):
                name = 'LocationFeatureSpecification' + name[len('Locationfeaturespecification'):]
            
            entity = base + ':' + name
        except:
            return entity
      
        
    return entity


def forward_entity_mapping(entity):
    
    return entity.upper()


def post_process_translation(_id, target_sent, prog):
    
    # remove extra quotation marks google translate adds
    # if target_sent[0] == '"':
    #     target_sent = target_sent[1:]
    # if target_sent[-1] == '"':
    #     target_sent = target_sent[:-1]
    
    # normalize all double quote symbols
    for token in ['&quot;', '""', '“', '”', '‘', '’', '「"', '"」', '「', '」']:
        target_sent = target_sent.replace(token, '"')
    
    target_sent = target_sent.replace('»', '')
    target_sent = target_sent.replace('«', '')
    target_sent = target_sent.strip()
    
    # in rare cases google translate drops quotes at the end of the sentence
    if target_sent.count('"') % 2 != 0:
        target_sent = target_sent + '"'
    
    # insert space before punctuation if not already there
    if target_sent[-1] in punctuation_string and target_sent[-1] != ' ':
        target_sent = target_sent[:-1] + ' ' + target_sent[-1]
    
    # insert space between quotation marks and their enclosed param value
    target_sent = re.sub(quoted_pattern_maybe_space, r'" \1 "', target_sent)
    
    # ' s --> 's
    target_sent = target_sent.replace("' s", "'s")
    
    # if english params are concatenated with non english characters (e.g. Chinese) split them
    # this can cause problems when the parameter is mixed language (e.g. "爸爸Kevin’s美式BBQ")
    # thus during augmentation we only accept parameters that are not mixed
    
    # also split entities and english tokens if concatenated
    
    if any([lang in args.param_language for lang in ['zh', 'ko', 'ja']]):
        
        new_target_sent = []
        for token in target_sent.split(' '):
            if len(english_regex.findall(token)):
                splitted_tokens = [w for w in english_regex.split(token) if w != '']
                new_target_sent.extend(splitted_tokens)
            elif len(entity_pattern.findall(token)):
                splitted_tokens = [w for w in entity_pattern.split(token) if w != '']
                new_target_sent.extend(splitted_tokens)
            else:
                new_target_sent.append(token)
        
        target_sent = ' '.join(new_target_sent)
        
        target_sent = target_sent

    if not args.no_lower_case:
        # lower case sentences unconditionally except for entities with backward_entity_mapping
        tokens = target_sent.split(' ')
        new_sent = []
        for token in tokens:
            if token == ' ':
                continue
            if entity_pattern.findall(token):
                for w in english_regex.split(token):
                    if w == '':
                        continue
                    elif entity_pattern.findall(w):
                        w = backward_entity_mapping(w)
                        new_sent.append(w)
                    else:
                        new_sent.append(w.lower())
            else:
                new_sent.append(token.lower())
        target_sent = ' '.join(new_sent)

    return _id, target_sent, prog


def get_parts(line):
    parts = tuple(map(lambda text: text.strip(), re.split(args.input_delimiter, line.strip())))
    return parts


def reduce_duplicate_progs(lines, f_out):
    prog2id_sent = defaultdict(list)
    
    orig_size = 0
    for line in lines:
        _id, sent, prog = get_parts(line)
        prog2id_sent[prog].append((_id, sent))
        orig_size += 1
    
    new_size = 0
    for prog, id_sent_list in prog2id_sent.items():
        if len(id_sent_list) <= args.sents_to_keep:
            selected_list = id_sent_list
        else:
            rand_indices = np.random.choice(list(range(len(id_sent_list))), args.sents_to_keep, replace=False).tolist()
            selected_list = [id_sent_list[i] for i in rand_indices]
        for _id, sent in selected_list:
            f_out.write('\t'.join([_id, sent, prog]) + '\n')
            new_size += 1
    
    print('The dataset size has been reduced from {} to {}'.format(orig_size, new_size))
    f_out.close()


def remove_duplicate_sents(lines, f_out):
    _ids, sents, progs = [], [], []
    for line in lines:
        _id, sent, prog = get_parts(line)
        _ids.append(_id)
        sents.append(sent)
        progs.append(prog)
    
    orig_size = len(sents)
    
    val_sets = set(sents)
    new_size = 0
    for _id, sent, prog in zip(_ids, sents, progs):
        if sent in val_sets:
            f_out.write('\t'.join([_id, sent, prog]) + '\n')
            val_sets.remove(sent)
            new_size += 1
    
    print('The dataset size has been reduced from {} to {}'.format(orig_size, new_size))
    f_out.close()


def compute_complexity(_id, sent, prog):
    params = 0
    joins = 0
    inString = False
    for token in prog.split(' '):
        if token == '"':
            inString = not inString
        if inString:
            continue
        if token.startswith('param:') and not token.startswith('param:distance'):
            params += 1
        elif token == 'join':
            joins += 1
    print(params + joins)
    return _id, sent, prog


def replace_ids(_id, sent, prog, count):
    return str(count + 1), sent, prog


def fix_punctuation(_id, sent, prog):
    # insert space before punctuation if not already
    if sent[-1] in punctuation_string and sent[-1] != ' ':
        sent = sent[:-1] + ' ' + sent[-1]
    
    return _id, sent, prog


def preprocess_paraphrased(_id, sent, prog):
    if _id[0] != 'A':
        return _id, sent, prog
    
    index = sent.find('-')
    if index != -1:
        sent = sent[:index] + ' - ' + sent[index + len('-'):]
    
    # remove apostrophe if at the end of a token
    sent = sent.replace("' ", " ")
    
    # remove apostrophe if at the end of a token
    sent = sent.replace("; ", " ")
    
    return _id, sent, prog


def arabic2english_digits(_id, sent, prog):
    for k, v in Ar2En_digit_map.items():
        sent = sent.replace(k, v)
    for k, v in Ar2En_digit_map.items():
        prog = prog.replace(k, v)
    return _id, sent, prog


def match_ids(_id, sent, prog, new_id):
    new_id = args.add_token + new_id
    return new_id, sent, prog


def refine_sentence(_id, context, sent, prog):
    
    # normalize japanese comma
    sent = sent.replace('：', ':')
    
    schema_pattern_1 = re.compile(r'GENERIC_ENTITY_ORG\.SCHEMA\.HOTEL:(.*?)LOCATIONFEATURESPECIFICATION')
    sent = re.sub(schema_pattern_1, r"\1 GENERIC_ENTITY_ORG.SCHEMA.HOTEL:LOCATIONFEATURESPECIFICATION", sent)

    schema_pattern_2 = re.compile(r'GENERIC_ENTITY_TT:(.*?)US_STATE_0')
    sent = re.sub(schema_pattern_2, r"\1 GENERIC_ENTITY_TT:US_STATE_0", sent)

    schema_pattern_4 = re.compile(r'LOCATIONFEATURESPECIFICATION_0(.*?). hotel: GENERIC_ENTITY_ORG.SCHEMA.HOTEL:')
    sent = re.sub(schema_pattern_4, r"\1 GENERIC_ENTITY_ORG.SCHEMA.HOTEL:LOCATIONFEATURESPECIFICATION_0", sent)
    
    
    fix_pattern = re.compile(r'GENERIC_ENTITY_ORG.SCHEMA.HOTEL\s*:\s*LOCATIONFEATURESPECIFICATION', re.IGNORECASE)
    sent = re.sub(fix_pattern, r"GENERIC_ENTITY_ORG.SCHEMA.HOTEL:LOCATIONFEATURESPECIFICATION", sent)
    
    schema_pattern_3 = re.compile(r'GENERIC_ENTITY_ORG\.SCHEMA(.*?)LOCATIONFEATURESPECIFICATION', re.IGNORECASE)
    sent = re.sub(schema_pattern_3, r"\1 GENERIC_ENTITY_ORG.SCHEMA.HOTEL:LOCATIONFEATURESPECIFICATION", sent)

    if 'the the' in sent:
        sent = sent.replace('the the', 'the')

    prog_value = duration_date_time_number_pattern.findall(prog)
    sent_value = duration_date_time_number_pattern.findall(sent)
    missing_values = [val for val in prog_value if val not in sent_value]
    
    if ('<' in sent or '>' in sent) and len(missing_values) == 0:
        # do another attempt but find missing values between quotations
        prog_value = quoted_pattern_with_space.findall(prog)
        sent_value = quoted_pattern_with_space.findall(sent)
        missing_values = [val for val in prog_value if val not in sent_value]
    
    if len(missing_values) > 1 and ('<' in sent or '>' in sent):
        print(_id, sent)
        print('Can not refine sentence based on the program entities')
    
    if len(missing_values) == 1:
        if '<' in sent:
            sent = sent.replace('<', ' ' + missing_values[0] + ' ')
        elif '>' in sent:
            sent = sent.replace('>', ' ' + missing_values[0] + ' ')
    
    _id, sent, prog = fix_punctuation(_id, sent, prog)
    
    sent = sent.replace('ي', 'ی')
    sent = sent.replace('ك', 'ک')
    
    prog = prog.replace('ي', 'ی')
    prog = prog.replace('ك', 'ک')
    
    # remove spaces from the beginning of the sentence
    while sent[0] == ' ':
        sent = sent[1:]
    
    translated_time_pattern = re.compile(r'(?:TIM|TEMPO|TEMP|THIM|THME|TMBER)_(\d)', re.IGNORECASE)
    sent = re.sub(translated_time_pattern, r"TIME_\1", sent)
    
    translated_number_pattern = re.compile(
        r'(?:NUMERO|NUMUMERI|NUMA|NUMBRE|numéro|n\s?ú\s?MERO|n\sú\sMER|NUMULARE)_(\d)', re.IGNORECASE)
    sent = re.sub(translated_number_pattern, r"NUMBER_\1", sent)
    
    translated_quoted_string_pattern = re.compile(r'(?:q\su\so\sTED_STRING|QUTED_STRING|QUODED_STRING)_(\d)', re.IGNORECASE)
    sent = re.sub(translated_quoted_string_pattern, r"QUOTED_STRING_\1", sent)
    
    translated_duration_string_pattern = re.compile(r'(?:DURAZIONE)_(\d)', re.IGNORECASE)
    sent = re.sub(translated_duration_string_pattern, r"DURATION_\1", sent)

    translated_location_pattern = re.compile(r'(?:LUCATION|LECATION|LIMATION|LAND|LOCCION)_(\d)', re.IGNORECASE)
    sent = re.sub(translated_location_pattern, r"LOCATION_\1", sent)
    
    # uppercase duration, date, time, number
    sent = re.sub(duration_date_time_number_pattern, lambda match: match.group(1).upper(), sent)
    
    for val in ['TIME', 'NUMBER', 'DATE', 'DURATION']:
        sent.replace('-{}'.format(val), '- {}'.format(val))
    
    sent = sent.replace('number_ ', 'NUMBER_0 ')
    sent = sent.replace('NUMBER_ ', 'NUMBER_0 ')
    sent = sent.replace(' UMBER_0', ' NUMBER_0')
    
    # only do for dialogs
    # sometimes TIME_0 is translated and not recovered by doing any of the previous heuristics
    if context:
        prog_value = duration_date_time_number_pattern.findall(prog)
        sent_value = duration_date_time_number_pattern.findall(sent)
        context_value = duration_date_time_number_pattern.findall(context)
        missing_values = [val for val in prog_value if val not in sent_value and val not in context_value]
        if len(missing_values) >= 1:
            sent = re.sub(re.compile(r'(?:TIM|TEMPO|TEMP|THIM|THME|MOMENTO|il\s\d+)', re.IGNORECASE), missing_values[0],
                          sent)
    
    return _id, sent, prog


def insert_space_quotes(_id, sent, prog):
    # insert spaces when either both or one space is missing
    new_sent = re.sub(quoted_pattern_maybe_space, r'" \1 "', sent)
    
    return _id, new_sent, prog


def fix_spaces_cjk(_id, sent, prog):
    if any([lang in args.param_language for lang in ['zh', 'ko', 'ja']]):
        output = []
        i = 0
        while i < len(sent):
            output.append(sent[i])
            if is_cjk(sent[i]) and i + 1 < len(sent) and sent[i + 1] != ' ':
                output.append(' ')
            elif not is_cjk(sent[i]) and i + 1 < len(sent) and is_cjk(sent[i + 1]):
                output.append(' ')
            i += 1
        sent = "".join(output)

        sent = sent.replace('  ', ' ')
        
    return _id, sent, prog


def remove_spaces_cjk(_id, sent, prog):
    # remove spaces in the sentence and program for CJK
    if any([lang in args.param_language for lang in ['zh', 'ko', 'ja']]):
        sent = sent.replace(' ', '')
        # if after removing both spaces we have entities concatenated
        # with english parameters split them
        new_target_sent = []
        for token in sent.split(' '):
            if len(entity_pattern.findall(token)):
                splitted_tokens = [w for w in entity_pattern.split(token) if w != '']
                new_target_sent.extend(splitted_tokens)
            else:
                new_target_sent.append(token)

        sent = ' '.join(new_target_sent)

        # reduce several spaces to just one
        sent = re.sub(multiple_space_pattern, ' ', sent)
        sent = sent.strip()
        
        # now program parameters
        # if after removing both spaces we have entities concatenated
        # with english parameters split them
        new_target_prog = []
        params = []
        in_string = False
        for token in prog.split(' '):
            if token == '"':
                if params:
                    new_target_prog.append("".join(params))
                new_target_prog.append('"')
                in_string = not in_string
                params = []
            elif in_string:
                params.append(token)
            else:
                new_target_prog.append(token)

        prog = ' '.join(new_target_prog)
        
    return _id, sent, prog


def remove_qpis(_id, sent, prog):
    if 'zh' in args.param_language:
        # remove quotes and spaces around them
        # sent = sent.replace(' " ', '')
        # if after removing both spaces we have entities concatenated
        # with english parameters split them
        new_target_sent = []
        for token in sent.split(' '):
            if len(entity_pattern.findall(token)):
                splitted_tokens = [w for w in entity_pattern.split(token) if w != '']
                new_target_sent.extend(splitted_tokens)
            else:
                new_target_sent.append(token)
        
        sent = ' '.join(new_target_sent)
    
    sent = sent.replace('"', '')
    
    # reduce several spaces to just one
    sent = re.sub(multiple_space_pattern, ' ', sent)
    sent = sent.strip()
    
    return _id, sent, prog


def remove_qpip_numbers(_id, sent, prog):
    prog = re.sub(quoted_number_pattern, r"\1", prog)
    new_prog = prog.replace('  ', ' ')
    
    return _id, sent, new_prog


def remove_qspace(_id, sent, prog):
    sent = re.sub(quoted_pattern_with_space, r'"\1"', sent)
    new_sent = sent.replace('  ', ' ')
    
    return _id, new_sent, prog


def process_oht(_id, sent, prog):
    sent = re.sub(re.compile(r'(?<!\_)\d+[\.|\-]\s*'), '', sent)
    
    for quote in ["“", "”", "‘", "’", "「", "」"]:
        sent = sent.replace(quote, '"')
    
    sent = re.sub(re.compile(r'(\"\s?\w+),'), r"\1 ,", sent)
    sent = re.sub(re.compile(r'(\"\s?\w+(?:\s\w+)*),'), r"\1 ,", sent)
    sent = re.sub(re.compile(r'(\"\s?\w+(?:\s\w+)*)\'s'), r"\1 's", sent)
    
    return _id, sent, prog

def prepare_for_marian(_id, sent, prog):
    # add quotation mark around capitalized Entities as well
    tokens = sent.split(' ')
    new_sent = []
    for token in tokens:
        if token == ' ':
            continue
        if entity_pattern.findall(token):
            new_sent.append('"')
            new_sent.append(token)
            new_sent.append('"')
        else:
            new_sent.append(token)
    target_sent = ' '.join(new_sent)

    return _id, target_sent, prog


def prepare_for_gt(_id, sent, prog):
    if sent.endswith('" ?'):
        sent = sent[:-1]
    
    # add triple quotation marks
    sent = re.sub(quoted_pattern_maybe_space, r'""" \1 """', sent)
    
    # replace entities with uppercase
    tokens = sent.split(' ')
    new_sent = []
    for token in tokens:
        if entity_pattern.findall(token):
            if token == '':
                continue
            for w in english_regex.split(token):
                if w == '':
                    continue
                elif entity_pattern.findall(w):
                    w = forward_entity_mapping(w)
                    new_sent.append(w)
                else:
                    new_sent.append(w.lower())
        else:
            new_sent.append(token.lower())
    sent = ' '.join(new_sent)
    
    new_sent = sent
    
    return _id, new_sent, prog


if __name__ == '__main__':
    
    if args.match_ids and not args.ref_file:
        raise ValueError('ref_file should be specified when doing match_ids')
    
    if args.ref_file:
        all_ref_ids = []
        with open(args.ref_file) as f_ref:
            for line in f_ref:
                _id = get_parts(line)[0]
                all_ref_ids.append(_id)
    
    with open(args.input_file, 'r', encoding='utf-8', errors='ignore') as f_in, open(args.output_file, 'w+') as f_out:
        lines = f_in.read().splitlines()
        if args.num_lines != -1:
            selected_lines = lines[:min(args.num_lines, len(lines))]
        else:
            selected_lines = lines
        
        if args.remove_duplicate_sents:
            remove_duplicate_sents(lines, f_out)
        
        elif args.reduce_duplicate_progs:
            reduce_duplicate_progs(lines, f_out)
        
        else:
            count = 0
            for line in tqdm(selected_lines):
                parts = get_parts(line)
                _id, context, sent, prog, extra = None, None, None, None, None
                if args.num_columns == 1:
                    sent = parts
                elif args.num_columns == 2:
                    _id, sent = parts
                elif args.num_columns == 3:
                    _id, sent, prog = parts[:3]
                    # if have more than one thingtalk annotation keep them
                    extra = parts[3:]
                elif args.num_columns == 4:
                    _id, context, sent, prog = parts[:4]
                    # if have more than one thingtalk annotation keep them
                    extra = parts[4:]
                else:
                    raise ValueError('input cannot have more than 4 columns!')
                
                # override sentence if empty
                if sent == "":
                    sent = "."
                
                if args.remove_qpis:
                    _id, sent, prog = remove_qpis(_id, sent, prog)
                if args.prepare_for_gt:
                    _id, sent, prog = prepare_for_gt(_id, sent, prog)
                if args.process_oht:
                    _id, sent, prog = process_oht(_id, sent, prog)
                if args.match_ids:
                    _id, sent, prog = match_ids(_id, sent, prog, all_ref_ids[count])
                if args.replace_ids:
                    _id, sent, prog = replace_ids(_id, sent, prog, count)
                if args.remove_qpip_numbers:
                    _id, sent, prog = remove_qpip_numbers(_id, sent, prog)
                if args.insert_space_quotes:
                    _id, sent, prog = insert_space_quotes(_id, sent, prog)
                if args.refine_sentence:
                    if args.num_columns == 4:
                        _id, sent, prog = refine_sentence(_id, context, sent, prog)
                    else:
                        _id, sent, prog = refine_sentence(_id, None, sent, prog)
                if args.fix_punctuation:
                    _id, sent, prog = fix_punctuation(_id, sent, prog)
                if args.compute_complexity:
                    _id, sent, prog = compute_complexity(_id, sent, prog)
                if args.remove_qspace:
                    _id, sent, prog = remove_qspace(_id, sent, prog)
                if args.preprocess_paraphrased:
                    _id, sent, prog = preprocess_paraphrased(_id, sent, prog)
                if args.remove_spaces_cjk:
                    _id, sent, prog = remove_spaces_cjk(_id, sent, prog)
                if args.post_process_translation:
                    _id, sent, prog = post_process_translation(_id, sent, prog)
                if args.prepare_for_marian:
                    _id, sent, prog = prepare_for_marian(_id, sent, prog)
                if args.fix_spaces_cjk:
                    _id, sent, prog = fix_spaces_cjk(_id, sent, prog)
                
                
                if not args.no_lower_case:
                    # lower case sentences unconditionally except for entities
                    tokens = sent.split(' ')
                    new_sent = []
                    for token in tokens:
                        if token == ' ':
                            continue
                        if entity_pattern.findall(token):
                            for w in english_regex.split(token):
                                if w == '':
                                    continue
                                elif entity_pattern.findall(w):
                                    new_sent.append(w)
                                else:
                                    new_sent.append(w.lower())
                        else:
                            new_sent.append(token.lower())
                    sent = ' '.join(new_sent)
                    
                if not args.no_unicode_normalize:
                    sent = unicodedata.normalize('NFD', sent)
                    if prog is not None:
                        prog = unicodedata.normalize('NFD', prog)
                    if context is not None:
                        context = unicodedata.normalize('NFD', context)
                    
                    if extra is not None:
                        new_extra = []
                        for item in extra:
                            new_extra.append(unicodedata.normalize('NFD', item))
                        extra = new_extra.copy()

                # reduce multiple spaces
                space_pattern = re.compile(r'\s{2,}')
                sent = re.sub(space_pattern, ' ', sent)

                if args.num_columns == 1:
                    f_out.write(sent + '\n')
                elif args.num_columns == 2:
                    f_out.write('\t'.join([_id, sent]) + '\n')
                elif args.num_columns == 3:
                    f_out.write('\t'.join([_id, sent, prog, *extra]) + '\n')
                elif args.num_columns == 4:
                    f_out.write('\t'.join([_id, context, sent, prog, *extra]) + '\n')
                
                count += 1
