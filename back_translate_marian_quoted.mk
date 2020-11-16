####################################################################################################################
##### back translate quoted dataset using Marian  ###########################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/marian/quoted/$(name).txt)

skip_translation ?= false

# Arabic  de-en es-en Farsi fi-en  it-en  Japanese  mul-en(pol) Turkish  zh-en

$(foreach name, $(all_names), $(experiment)/oht/%/marian/quoted/$(name)):
	mkdir -p $(experiment)/oht/$*/marian/quoted
	# prepare quoted data for back translation to English
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_marian --input_file $(experiment)/oht/$*/quoted/$$f.tsv --output_file ./$(experiment)/oht/$*/marian/quoted/$$f.tsv.tmp ; done

	for f in $(all_names) ; do cut -f1,2 ./$(experiment)/oht/$*/marian/quoted/$$f.tsv.tmp > ./$(experiment)/oht/$*/marian/quoted/$$f.tsv ; rm -rf ./$(experiment)/oht/$*/marian/quoted/$$f.tsv.tmp ; done


$(experiment)/oht/%/marian/quoted-back: $(foreach name, $(all_names), $(experiment)/oht/%/marian/quoted/$(name))
	mkdir -p $@

	# batch translate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			python3 $(genienlp) run-paraphrase $(default_translation_hparams) --temperature 0.3 --model_name_or_path Helsinki-NLP/opus-mt-$*-en --src_lang $* --tgt_lang en --input_file $(experiment)/oht/$*/marian/quoted/$$f.tsv --output_file $@/$$f.tsv
		done ; \
	fi


$(experiment)/oht/%/marian/quoted-unrefined-back: $(experiment)/oht/%/marian/quoted-back
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do paste $(experiment)/oht/$*/marian/quoted-back/$$f.tsv $(experiment)/en/quoted-uniq-progs/$$f.tsv >  $@/$$f.tsv ; done


$(experiment)/oht/%/marian/quoted-back-cleaned: $(experiment)/oht/%/marian/quoted-unrefined-back
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/marian/quoted-back-augmented-unrefined: $(experiment)/oht/%/marian/quoted-back-cleaned
	mkdir -p $@
	# augment (=unquote) qpis inputs with actual parameter values

	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale en -l en-US $(default_augment_train_hparams) $<$$f.tsv  ; \
		else \
			$(genie) augment -o $@/$$f.tsv --param-locale en -l en-US $(default_augment_evaltest_hparams) $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/oht/%/marian/final-back: $(experiment)/oht/%/marian/quoted-back-augmented-unrefined
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


back_translate_marian_quoted_%: $(experiment)/oht/%/marian/final-back

	# done!
	echo $@


back_translate_marian_quoted_all_langs:
	for lang in $(marian_oht_languages) ; do \
		make -B back_translate_marian_quoted_$$lang ; \
	done
