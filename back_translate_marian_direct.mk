####################################################################################################################
##### back translate direct dataset using Marian  ###########################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/marian/direct/$(name).txt)

skip_translation ?= false

# Arabic  de-en es-en Farsi fi-en  it-en  Japanese  mul-en(pol) Turkish  zh-en

$(foreach name, $(all_names), $(experiment)/oht/%/marian/direct/$(name)):
	mkdir -p $(experiment)/oht/$*/marian/direct
	# prepare quoted data for back translation to English
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_marian --num_columns 3 --input_file $(experiment)/oht/$*/final/$$f.tsv --output_file ./$(experiment)/oht/$*/marian/direct/$$f.tsv ; done


$(experiment)/oht/%/marian/direct-back: $(foreach name, $(all_names), $(experiment)/oht/%/marian/direct/$(name))
	mkdir -p $@

	# batch translate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			python3 $(genienlp) run-paraphrase --cache_dir $(GENIENLP_EMBEDDINGS) --batch_size 50 --temperature 0.4 --id_column 0 --output_example_ids_too --input_file $(experiment)/oht/$*/marian/direct/$$f.tsv --input_column 1 --gold_column 1 --output_file $@/$$f.tsv --model_name_or_path Helsinki-NLP/opus-mt-$*-en --src_lang $* --tgt_lang en --repetition_penalty 1.0 --num_samples 1 --skip_heuristics --att_pooling mean --task translate --return_attentions ; \
		done ; \
	fi


$(experiment)/oht/%/marian/direct-unrefined-back: $(experiment)/oht/%/marian/direct-back
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do cut -f3 $(experiment)/oht/$*/final/$$f.tsv | paste $(experiment)/oht/$*/marian/direct-back/$$f.tsv - >  $@/$$f.tsv ; done


$(experiment)/oht/%/marian/direct-back-cleaned: $(experiment)/oht/%/marian/direct-unrefined-back
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/marian/final-direct-back: $(experiment)/oht/%/marian/direct-back-cleaned
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


back_translate_marian_direct_%: $(experiment)/oht/%/marian/final-direct-back

	# done!
	echo $@


back_translate_marian_direct_all_langs:
	for lang in $(marian_oht_languages) ; do \
		make -B back_translate_marian_direct_$$lang ; \
	done
