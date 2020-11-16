####################################################################################################################
##### back translate unquoted dataset using Marian  ###########################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/marian/unquoted/$(name).txt)

skip_translation ?= false

# Arabic  de-en es-en Farsi fi-en  it-en  Japanese  mul-en(pol) Turkish  zh-en

$(foreach name, $(all_names), $(experiment)/oht/%/marian/unquoted/$(name)):
	mkdir -p $(experiment)/oht/$*/marian/unquoted
	# prepare quoted data for back translation to English
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_marian --num_columns 2 --input_file $(experiment)/oht/$*/input/$$f.txt --output_file ./$(experiment)/oht/$*/marian/unquoted/$$f.tsv ; done


$(experiment)/oht/%/marian/unquoted-back: $(foreach name, $(all_names), $(experiment)/oht/%/marian/unquoted/$(name))
	mkdir -p $@

	# batch translate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			python3 $(genienlp) run-paraphrase $(default_translation_hparams) --temperature 0.3 --model_name_or_path Helsinki-NLP/opus-mt-$*-en --src_lang $* --tgt_lang en --input_file $(experiment)/oht/$*/marian/unquoted/$$f.tsv --output_file $@/$$f.tsv
		done ; \
	fi


$(experiment)/oht/%/marian/unquoted-unrefined-back: $(experiment)/oht/%/marian/unquoted-back
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do cut -f3 $(experiment)/en/input/$$f.tsv | paste $(experiment)/oht/$*/marian/unquoted-back/$$f.tsv - >  $@/$$f.tsv ; done


$(experiment)/oht/%/marian/unquoted-back-cleaned: $(experiment)/oht/%/marian/unquoted-unrefined-back
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/marian/unquoted-back-cleaned-quoted: $(experiment)/oht/%/marian/unquoted-back-cleaned
	mkdir -p $@
	# quote dataset as sanity check
	for f in $(all_names) ; do $(genie) requote $(contextual) --mode replace -o $@/$$f.tsv $</$$f.tsv ; done


$(experiment)/oht/%/marian/unquoted-back-augmented-unrefined: $(experiment)/oht/%/marian/unquoted-back-cleaned
	mkdir -p $@
	# only replace numbers

	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale en -l en-US $(default_augment_train_hparams) $<$$f.tsv  ; \
		else \
			$(genie) augment -o $@/$$f.tsv --param-locale en -l en-US $(default_augment_evaltest_hparams) $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/oht/%/marian/final-unquoted-back: $(experiment)/oht/%/marian/unquoted-back-augmented-unrefined
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


back_translate_marian_unquoted_%: $(experiment)/oht/%/marian/final-unquoted-back $(experiment)/oht/%/marian/unquoted-back-cleaned-quoted

	# done!
	echo $@


back_translate_marian_unquoted_all_langs:
	for lang in $(marian_oht_languages) ; do \
		make -B back_translate_marian_$$lang ; \
	done
