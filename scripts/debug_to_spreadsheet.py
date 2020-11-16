from argparse import ArgumentParser
import os
import xlsxwriter

parser = ArgumentParser()

parser.add_argument('--input_folder', default='./restaurants/test/', type=str)
parser.add_argument('--output_folder', default='./restaurants/test/exp5/',  type=str)
parser.add_argument('--english_input_file', type=str)
parser.add_argument('--column', default=1, type=int)
parser.add_argument('--base_form', default='xlmr-exp5')
parser.add_argument('--add_lang_to_file', action='store_true')
parser.add_argument('--contextual', action='store_true')

args = parser.parse_args()

fieldnames = tuple(['id', 'message', 'sentence', 'english_sentence', 'gold', 'predicted', 'how to fix?'])
field2part = {0:0, 1:1, 2:2, 4:3, 5:4}
num_cols = len(fieldnames)

workbook = xlsxwriter.Workbook(os.path.join(args.output_folder, 'debug.xlsx'))

if not os.path.exists(args.output_folder):
    os.makedirs(args.output_folder, exist_ok=True)
    
def process_id_contextual(value):
    base, rest = value.split('/', 1)
    while base[:2] == 'RS':
        base = base[2:]
    turn = rest.split('-', 1)[0]
    return base + '/' + turn

def process_id(value):
    base = value.split('-', 1)[0]
    if base.startswith('RST'):
        base = base[3:]
    if base.startswith('RS'):
        base = base[2:]
    if base[0] == 'S':
        base = base[1:]
    if base[0] == 'R':
        base = base[1:]
    return base
    

english_id2sent = {}
with open(args.english_input_file, 'r') as f_in:
    for line in f_in:
        parts = list(map(lambda part: part.strip(), line.split('\t')))
        if args.contextual:
            _id, context, sentence, program = parts[:4]
            _id = process_id_contextual(_id)
        else:
            _id, sentence, program = parts[:3]
            _id = process_id(_id)
            
        english_id2sent[_id] = sentence
        
for lang_folder in os.listdir(args.input_folder):
    for file in os.listdir(os.path.join(args.input_folder, lang_folder)):
        full_path = os.path.join(*[args.input_folder, lang_folder, file])
        if not os.path.isfile(full_path):
            continue
        row_dicts = []
        if args.base_form in file and file.endswith('.debug'):
            with open(full_path, 'r') as f_in:
                # for some experiments like emmlp20 multilingual exp5 you train one model
                # and test on other languages thus the model name is the same but test sets are different
                # we will append lang_folder name to file in those cases
                if args.add_lang_to_file:
                    file = file[:-len('.debug')] + '-' + lang_folder + '.debug'
                worksheet = workbook.add_worksheet(name=file)
                for i, field in enumerate(fieldnames):
                    worksheet.write_string(0, i, fieldnames[i])
                row = 1
                for line in f_in:
                    parts = list(map(lambda part: part.strip(), line.split('\t')))
                    if args.contextual:
                        _id = process_id_contextual(parts[0])
                    else:
                        _id = process_id(parts[0])
                    for col in range(0, num_cols):
                        if fieldnames[col] == 'how to fix?':
                            # write empty cell for how to fix column
                            worksheet.write_string(row, col, '')
                        elif fieldnames[col] == 'english_sentence':
                            # write empty cell for how to fix column
                            worksheet.write_string(row, col, english_id2sent[_id])
                        else:
                            worksheet.write_string(row, col, parts[field2part[col]])

                    row += 1

workbook.close()










