[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green)](https://github.com/stanford-oval/SPL/blob/master/LICENSE)

# Semantic Parser Localizer (SPL) 

This repository contains the code implementation for SPL, as described in:

[_Localizing Open-Ontology QA Semantic Parsers in a Day Using Machine Translation_](https://www.aclweb.org/anthology/2020.emnlp-main.481/) <br/> Mehrad Moradshahi, Giovanni Campagna, Sina J. Semnani, Silei Xu, Monica S. Lam <br/>

### Abstract

Semantic Parser Localizer (SPL) is a toolkit that leverages Neural Machine Translation (NMT) systems to localize a semantic parser for a new language. Our methodology is to (1) generate training data automatically in the target language by augmenting machine-translated datasets with local entities scraped from public websites, (2) add a few-shot boost of human-translated sentences and train a novel XLMR-LSTM semantic parser, and (3) test the model on natural utterances curated using human translators.<br/>
We assess the effectiveness of our approach by extending the current capabilities of Schema2QA, a system for English Question Answering (QA) on the open web, to 10 new languages for the restaurants and hotels domains. We show our approach outperforms the previous state-of-the-art methodology by more than 30% for hotels and 40% for restaurants with localized ontologies.<br/>
Our methodology enables any software developer to add a new language capability to a QA system for a new domain, leveraging machine translation, in less than 24 hours.

### Methodology

This plot shows the data generation pipeline used to produce
train and validation splits in a new language such as
Italian. Given an input sentence in English and its annotation in the formal ThingTalk query language, SPL generates multiple examples in the
target language with localized entities.

<p align="center">
<img src="https://github.com/stanford-oval/SPL/blob/master/images/multilingual-pipeline.png" width="400" >
</p>

### Results

Exact match accuracy for 10 languages (Restaurants domain)

<p align="center">
<img src="https://github.com/stanford-oval/SPL/blob/master/images/chart-restaurants.png" width="1000" >
</p>

## Quickstart

### Setup:
1. Clone the following repositories into your desired folder ($SRC_DIR):
```bash
cd ${SRC_DIR}
git clone https://github.com/Mehrad0711/SPL.git
git clone https://github.com/stanford-oval/genienlp.git
git clone https://github.com/stanford-oval/genie-toolkit.git
```

2. Follow the installation guide in [genie-toolkit](https://github.com/stanford-oval/genie-toolkit) repo to install the dependencies.

3. For each repository, the following commit hashes should be used to reproduce the results:
    - genienlp (c6ffb08742fed0c414d6ffc5eeae679cabdb20ff)
    - genie-toolkit (7a74010f8c51c8b0dc1c7f5e604a8af742b00a29)
    - genie-k8s (fb6a27a8945a3a43a563702f7809669f802a071f)

4. If you want to do translations for a new language, you need access to a Google Cloud account with permission to use Cloud Translation API.
Please look here for a [quick setup](https://cloud.google.com/translate/docs/quickstarts). You need to keep your credential file for authentication and create a project.

5. Navigate to `SPL` directory:
```bash
cd $SRC_DIR/SPL
```

6. Open project_config.mk and set paths to the location you have stored the repositories and files. You also need to provide the project_id you set up in step 3. This file contains the main configurations for running the experiments.

7. `dataset` directory should contain splits (train/ eval/ test) of original English dataset per domain.

### Processing

1. Clean the current directory:
```bash
make deepclean
```

2. Collect parameters and entities for your desired language: In project.config set `$(experiment)_$(language)_init_url`, `$(experiment)_$(language)_base_url`, `$(experiment)_$(language)_url_pattern` to websites you wish to crawl for their schemas.
Then run the following command which produces raw schema in json format. (Run for both English and the foreign language)
 ```bash
make experiment=${experiment} crawl_target_size=100 schema_crawl_en
make experiment=${experiment} crawl_target_size=100 schema_crawl_${language}
```

3. Create parameter-datasets for each experiment:
 ```bash
make experiment=${experiment} subset_languages=en ${experiment}/parameter-datasets.tsv
make -B experiment=${experiment} subset_languages=${language} ${experiment}/parameter-datasets.tsv
```

4. Process English dataset and prepare data splits to be translated:
```bash
make -B process_data
```
This will create `en` folder and perform multiple transformations on the splits of original dataset and stores the output files in corresponding subfolders.

5. You now need to upload your dataset to a Google Cloud Storage. You can create one in your GC console if you don't have one already. You may set you project_id, project_number, and credential_file as defaults in `scripts/translate_v3.py` so that you don't have to pass it everytime you call `translate_v3.py`
Please follow these [guidlines](https://cloud.google.com/storage/docs/naming-buckets#:~:text=Bucket%20names%20must%20contain%20only,Names%20containing%20dots%20require%20verification.) for bucket naming.
```bash
make input_bucket=${my_bucket} experiment=${experiment} ${experiment}/upload_data
```

6. If you want to use a glossary for translation, you should set glossary_type to manual and put your glossary file here: `$(dataset_folder)/extras/` OR set glossary_type to default.
Default mode will create a glossary file from your input data automatically by extracting the entities and using that token for all languages. 
```bash
make glossary_type=${glossary_type} all_languages='${languages}' experiment=${experiment} ${experiment}/upload_glossary
```

7. Now you are ready for translation:

```bash
make experiment=${experiment} input_bucket=${my_bucket} batch_translate_with_glossary_{language}
``` 
This will create `${experiment}/translated/${lang}` folder and perform several transformations on the splits of input dataset and stores them in corresponding subfolders.


### Training and Evaluation

These instructions are meant to be used with [genie-k8s](https://github.com/stanford-oval/genie-k8s) to train and evaluate models on kubernetes.
You may adapt or use your own scripts for training/ evaluation.

1. Training: </br>
You can run multiple models on multiple datasets in parallel. First you need to create a text file containing the hyperparameter values for each experiment.</br>
You should then put that file in this directory: `$(multilingualdir)/extras/` and set `restaurants_train_args_name` to the file name.</br>
You should also specify your model name prefix `restaurants_model_prefix` and the datasets you want to use for training `restaurants_train_datasets`. Finally you can evaluate each model on all training datasets by running:
```bash
make train-all
```
This command will use genie-k8s repo to run the experiments.

2. Evaluation: </br>
After training is done you can evaluate those models on your desired dev/ test datasets by setting `restaurants_eval_datasets` and running:
```bash
make eval-all
```
This command will run evaluation on both test and dev sets. If you want to run evaluation on only one split, you can do so by running:
```bash
make eval-all-${split_set}
```

3. Once all the evaluations are done, you can retrieve the results by running:
```bash
make print-eval-results
```
This will print all the results in `print-eval-results` file.


## Pretrained models and datasets

You can download our datasets and pretrained models for both domains by running:
```bash
make download_release_files
```

This will download and unzip the dataset and models to `spl-release` directory. After unzipping, you will have one subfolder for each language.

English dataset contains _train_ and _eval_ splits. _Train_ set contains both synthetic sentences and crowdsourced paraphrases. _Eval_ split only contain crowdsourced examples.

Other languages contain _train_, _eval_, _eval_mt_, and _eval_comb_ splits. _Test_ splits are reserved for benchmarking. _Train_ and _eval_mt_ splits contain only machine translated sentences from the corresponding splits of English dataset. We chose ~2/3 of English eval examples and collected human translation for them. _Eval_ split contains these human translated examples as well as machine translated examples for the remaining 1/3 (mainly to keep the size of eval set the same across experiments and avoid bias). We then combine _eval_mt_ and _eval_ to from _eval_comb_ (this split is used for validation in the paper experiments). _Test_ dataset is all human translated.</br>

Please refer to our [paper](https://www.aclweb.org/anthology/2020.emnlp-main.481/) for more details on the dataset and experiments.

## FAQ

When running the code I get`Error: Cannot find module '/Users/Mehrad/Documents/genie-toolkit/tool/genie.js'`</br>
- Change 'geniedir' in project.config to point to the directory where you've downloaded genie-toolkit library.

Google translation process is taking longer than expected.</br>
- You can query its status via HTTP calls. Please see [link](https://cloud.google.com/translate/docs/advanced/long-running-operation)


## Copyright 

The schema samples provided in `schema_data_sampled` were taken from third-party websites, and is copyrighted by the respective author.</br>
We're releasing this data for non-profit, educational purposes only. The copyright owner can contact us to have it taken down, if they so wish.


## Citation
If you use the software in this repository, please cite:

```
@inproceedings{moradshahi-etal-2020-localizing,
    title = "Localizing Open-Ontology {QA} Semantic Parsers in a Day Using Machine Translation",
    author = "Moradshahi, Mehrad and Campagna, Giovanni and Semnani, Sina and Xu, Silei and Lam, Monica",
    booktitle = "Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
    month = November,
    year = "2020",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/2020.emnlp-main.481",
    pages = "5970--5983",
}
```
