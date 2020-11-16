# Part of this code has been adapted from Google Cloud Platform GitHub codebase
# https://github.com/GoogleCloudPlatform/python-docs-samples/tree/master/translate/cloud-client
#
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


import shutil
import re
import argparse
import os
import sys

sys.path.append('../')
from re_patterns import *

from google.cloud import translate
from google.cloud import storage


def create_default_glossary(input_local_path, input_names, glossary_local_path, source_lang, target_langs, translate_params,  glossary_name, special_words=set()):
    languages = [source_lang] + target_langs
    entity_regex = re.compile(r'[A-Z].*?_[0-9]+')
    param_regex = re.compile('\"\s((?:[^"]|\\.)+?)\s\"')
    entities = set()
    parameters = set()
    entry_count = 0
    for input_name in input_names:
        with open(os.path.join(input_local_path, input_name), 'r') as f_in:
            for line in f_in:
                sentence = line.split('\t')[1]
                entities.update(re.findall(entity_regex, sentence))
                # replace ',' with ';' to avoid splitting values when google creates the glossary
                # but then the values in the sentence will not be preserved if they contain ','
                # it's best to use param values that do not contain this token
                if translate_params:
                    parameters.update(map(lambda param: param.replace(',', ';'), re.findall(param_regex, sentence)))
                    
            if not os.path.isdir(glossary_local_path):
                os.mkdir(glossary_local_path)
            with open(os.path.join(glossary_local_path, glossary_name), 'w') as f_out:
                f_out.write(','.join(languages) + '\n')
                if len(special_words) == 0 and len(entities) == 0 and len(parameters) == 0:
                    print('Defauly glossary has 0 entries. Hence, we will upload a dummy glossary to prevent errors.')
                    f_out.write(','.join(['yt33hNAu4a5k']*len(languages)) + '\n')
                else:
                    all_values = set().union(*[special_words, entities, parameters])
                    entry_count = len(all_values)
                    for word in parameters:
                        f_out.write(','.join(['""" ' + word + ' """']*len(languages)) + '\n')
                    for word in entities:
                        f_out.write(','.join([word]*len(languages)) + '\n')
                    for word in special_words:
                        f_out.write(','.join([word]*len(languages)) + '\n')
                        
                        
    print(u"Entry count: {}".format(entry_count))
                

def get_glossary(project_id, glossary_id):
    """Get a particular glossary based on the glossary ID."""

    name = TRANSLATION_CLIENT.glossary_path(project_id, "us-central1", glossary_id)
    
    try:
        response = TRANSLATION_CLIENT.get_glossary(name)
        print(u"Glossary name: {}".format(response.name))
        print(u"Input URI: {}".format(response.input_config.gcs_source.input_uri))
        return True
    except:
        return False


def get_ids(input_local_path, input_name):
    ids = []
    with open(os.path.join(input_local_path, input_name), 'r') as f_in:
        for line in f_in:
            ids.append(line.split('\t')[0])
    return ids


def find_mapping(original_ids, permuted_ids):
    assert len(original_ids) == len(permuted_ids)
    assert set(original_ids) == set(permuted_ids)
    mapping = {}
    for i, id in enumerate(original_ids):
        mapping[i] = permuted_ids.index(id)
    return mapping


def get_blob_name(uri):
    return uri.rsplit('/', 1)[1]


def download_results(bucket_name, destination_folder, input2origids, use_glossary, keep_blob_name=False, remove_output_id=False):
    """Download all blobs from the bucket."""
    
    bucket = STORAGE_CLIENT.bucket(bucket_name)
    index_blob = bucket.get_blob("index.csv")
    index_blob.download_to_filename(os.path.join(destination_folder, "index.csv"))
    result = index_blob.download_as_string().decode('utf-8').strip('\n').split('\n')
    output2input = dict()
    output2lang = dict()
    for line in result:
        input_uri, language, output_uri = line.split(',')[:3]
        output2input[get_blob_name(output_uri)] = get_blob_name(input_uri)
        output2lang[get_blob_name(output_uri)] = language

    for blob in list_blobs(bucket_name):
        blob_name = blob.name
        if blob_name == 'index.csv':
            continue
        ids = []
        target_sents = []
        result = blob.download_as_string().decode('utf-8').strip('\n').split('\n')
        for line in result:
            line_parsed = list(map(lambda line: line.strip(), line.strip().split('\t')))
            if use_glossary:
                id, source_sent, target_sent_no_glossary, target_sent = line_parsed[:4]
            else:
                # first see if you have translated with glossary file already
                if len(line_parsed) == 4:
                    id, source_sent, target_sent_no_glossary, _ = line_parsed[:4]
                    target_sent = target_sent_no_glossary
                else:
                    id, source_sent, target_sent = line_parsed[:3]
            ids.append(id)
            # target_sent = post_process_sent(target_sent, language=output2lang[blob_name])
            target_sent = target_sent
            target_sents.append(target_sent)
        mapping = find_mapping(input2origids[output2input[blob_name]], ids)
        with open(os.path.join(destination_folder, blob_name if keep_blob_name else output2input[blob_name]), 'w') as f_out:
            for i in range(len(mapping)):
                index = mapping[i]
                if remove_output_id:
                    f_out.write(target_sents[index] + '\n')
                else:
                    f_out.write('T' + ids[index] + '\t' + target_sents[index] + '\n')

    print("All blobs from bucket {} downloaded to {}".format(bucket_name, destination_folder))


def upload_blob(bucket_name, input_local_path, input_names):
    """Uploads a file to the bucket."""

    bucket = STORAGE_CLIENT.bucket(bucket_name)
    if not bucket_exists(bucket_name):
        create_bucket(bucket_name)
        
    if isinstance(input_names, str):
        input_names = [input_names]
    
    for input_name in input_names:
        blob = bucket.blob(input_name)
        blob.upload_from_filename(os.path.join(input_local_path, input_name))
        print("File {} uploaded to {}".format(input_name, os.path.join('gs://', bucket_name, input_name)))


def list_blobs(bucket_name):
    """Lists all the blobs in the bucket."""

    blobs = STORAGE_CLIENT.list_blobs(bucket_name)

    return blobs


def delete_blobs(bucket_name):
    """Lists all the blobs in the bucket."""

    bucket = STORAGE_CLIENT.bucket(bucket_name)
    bucket_blobs = list_blobs(bucket.name)
    bucket.delete_blobs(bucket_blobs)


def bucket_exists(bucket_name):
    try:
        STORAGE_CLIENT.get_bucket(bucket_name)
        return True
    except:
        return False
    
    
def create_bucket(bucket_name, bucket_location='us-west2'):
    STORAGE_CLIENT.create_bucket(bucket_name, location=bucket_location)


def delete_bucket(bucket_name):
    bucket = STORAGE_CLIENT.get_bucket(bucket_name)
    bucket.delete(force=True)


def sample_list_glossaries(project_id):
    """List Glossaries."""

    parent = TRANSLATION_CLIENT.location_path(project_id, "us-central1")

    # Iterate over all results
    for glossary in TRANSLATION_CLIENT.list_glossaries(parent):
        print("Name: {}".format(glossary.name))
        print("Entry count: {}".format(glossary.entry_count))
        print("Input uri: {}".format(glossary.input_config.gcs_source.input_uri))

        # Note: You can create a glossary using one of two modes:
        # language_code_set or language_pair. When listing the information for
        # a glossary, you can only get information for the mode you used
        # when creating the glossary.
        for language_code in glossary.language_codes_set.language_codes:
            print("Language code: {}".format(language_code))


def upload_term_set_glossary(project_id, glossary_uri, glossary_id, source_lang, target_langs):

    # Supported language codes: https://cloud.google.com/translate/docs/languages
    source_lang_code = source_lang
    target_lang_code = target_langs
    all_languages = [source_lang_code] + target_lang_code
    location = "us-central1"  # The location of the glossary

    name = TRANSLATION_CLIENT.glossary_path(project_id, location, glossary_id)
    if get_glossary(project_id, glossary_id):
        print('Overwrite glossary files')
        operation = TRANSLATION_CLIENT.delete_glossary(name)
        result = operation.result(timeout=180)
        print("Deleted: {}".format(result.name))

    language_codes_set = translate.types.Glossary.LanguageCodesSet(
        language_codes=all_languages
    )

    gcs_source = translate.types.GcsSource(input_uri=glossary_uri)

    input_config = translate.types.GlossaryInputConfig(gcs_source=gcs_source)

    glossary = translate.types.Glossary(
        name=name, language_codes_set=language_codes_set, input_config=input_config
    )

    parent = TRANSLATION_CLIENT.location_path(project_id, location)

    operation = TRANSLATION_CLIENT.create_glossary(parent=parent, glossary=glossary)

    result = operation.result(timeout=180)
    print("Created: {}".format(result.name))
    print("Input Uri: {}".format(result.input_config.gcs_source.input_uri))


def sample_batch_translate_text_with_glossary_and_model(
    input_uris,
    output_uri,
    project_id,
    location,
    target_language,
    source_language,
    model_id,
    glossary_id,
    use_glossary
):
    """
    Batch translate text with Glossary and Translation model
    """

    target_language_codes = target_language
    
    input_configs = []
    for i in range(len(input_uris)):
        gcs_source = {"input_uri": input_uris[i]}
        # Can be "text/plain" or "text/html"
        mime_type = "text/plain"
        input_configs_element = {"gcs_source": gcs_source, "mime_type": mime_type}
        input_configs.append(input_configs_element)
        
    gcs_destination = {"output_uri_prefix": output_uri}
    output_config = {"gcs_destination": gcs_destination}
    parent = TRANSLATION_CLIENT.location_path(project_id, location)

    if model_id:
        models = {}
        for lang in target_language_codes:
            model_path = 'projects/{}/locations/{}/models/{}'.format(project_id, 'us-central1', model_id)
            models[lang] = model_path
    else:
        # use default model (= nmt)
        models = None

    glossary_path = TRANSLATION_CLIENT.glossary_path(project_id, 'us-central1', glossary_id)

    glossary_config = translate.types.TranslateTextGlossaryConfig(glossary=glossary_path)
    glossaries = {}
    for lang in target_language_codes:
        glossaries[lang] = glossary_config
        
    if not use_glossary:
        glossaries = None

    operation = TRANSLATION_CLIENT.batch_translate_text(
        parent=parent,
        source_language_code=source_language,
        target_language_codes=target_language_codes,
        input_configs=input_configs,
        output_config=output_config,
        models=models,
        glossaries=glossaries
    )

    print("Waiting for translation to complete...")
    response = operation.result()

    # Display the translation for each input text provided
    print(u"Total Characters: {}".format(response.total_characters))
    print(u"Translated Characters: {}".format(response.translated_characters))


def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("--input_bucket", type=str, default="almond_dataset")
    parser.add_argument("--input_local_path", type=str, default="./")
    parser.add_argument("--input_names", type=str, nargs='+', default=["input.tsv"])
    parser.add_argument('--output_bucket', type=str, default="almond_output")
    parser.add_argument("--glossary_local_path", type=str, default="./extras/")
    parser.add_argument("--glossary_name", type=str, default="glossary.csv")
    parser.add_argument("--glossary_bucket", type=str, default="almond_glossary")
    parser.add_argument("--project_id", type=str, default="")
    parser.add_argument("--project_number", type=str, default="")
    parser.add_argument("--location", type=str, default="us-central1")
    parser.add_argument("--source_lang", type=str, default="en")
    parser.add_argument("--target_langs", type=str, nargs='+', default=["fa"])
    parser.add_argument("--model_id", type=str, default="")
    parser.add_argument("--glossary_type", type=str, choices=['default', 'manual'], default="default")

    parser.add_argument("--update_glossary", action='store_true')
    parser.add_argument("--no_glossary", action='store_true')
    parser.add_argument('--no_translate_params', action='store_true')
    parser.add_argument("--update_dataset", action='store_true')
    parser.add_argument("--do_translate", action='store_true')
    parser.add_argument("--download_results", action='store_true')
    parser.add_argument("--remove_output_id", action='store_true')
    parser.add_argument("--overwrite_output", action='store_true')
    
    parser.add_argument("--output_local_path", type=str, default="./translation_results")
    parser.add_argument("--keep_blob_name", action='store_true', help="output files names is same as their blob names")

    parser.add_argument('--credential_file', default='', type=str)
    args = parser.parse_args()

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = args.credential_file
    
    global TRANSLATION_CLIENT
    global STORAGE_CLIENT
    
    TRANSLATION_CLIENT = translate.TranslationServiceClient()
    STORAGE_CLIENT = storage.Client()
    
    if args.update_glossary or args.do_translate:
        
        if args.glossary_type == 'default':
            glossary_name = 'default.csv'
        else:
            glossary_name = args.glossary_name
        
        glossary_id = glossary_name.rsplit('.', 1)[0] + '_id'


    if args.update_glossary:
        
        if args.glossary_type == 'default':
             create_default_glossary(args.input_local_path, args.input_names,
                                     args.glossary_local_path, args.source_lang,
                                     args.target_langs, not args.no_translate_params, glossary_name, special_words=set())
    
        glossary_uri = os.path.join(*['gs://', args.glossary_bucket, glossary_name])
        upload_blob(args.glossary_bucket, args.glossary_local_path, glossary_name)
        upload_term_set_glossary(args.project_id, glossary_uri, glossary_id, args.source_lang, args.target_langs)


    if args.update_dataset:
        upload_blob(args.input_bucket, args.input_local_path, args.input_names)
    
    use_glossary = True
    if args.no_glossary:
        use_glossary = False

    if args.do_translate:

        if bucket_exists(args.output_bucket):
            if args.overwrite_output:
                delete_blobs(args.output_bucket)
        else:
            create_bucket(args.output_bucket)

        input_uris = []
        for input_name in args.input_names:
            input_uris.append(os.path.join(*['gs://', args.input_bucket, input_name]))
        output_uri = os.path.join(*['gs://', args.output_bucket + '/'])

        sample_batch_translate_text_with_glossary_and_model(
            input_uris,
            output_uri,
            args.project_id,
            args.location,
            args.target_langs,
            args.source_lang,
            args.model_id,
            glossary_id,
            use_glossary
        )
        
    if args.download_results:

        input2origids = dict()
        for input_name in args.input_names:
            input2origids[input_name] = get_ids(args.input_local_path, input_name)
        
        output_path = args.output_local_path
        os.makedirs(output_path, exist_ok=True)
        
        download_results(args.output_bucket, output_path, input2origids, use_glossary, args.keep_blob_name, args.remove_output_id)

if __name__ == '__main__':
    main()

