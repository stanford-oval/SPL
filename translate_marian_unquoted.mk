####################################################################################################################
##### translate dialogs using Marian MT models ###################################################################
####################################################################################################################

# list of models
# en-ar en-de en-es Farsi en-fi  en-it  Japanese  en-mul(pol) Turkish  en-zh

$(foreach name, $(all_names), $(experiment)/marian/%/unquoted-qpis-translated/$(name)):
	mkdir -p $(experiment)/marian/$*/unquoted-qpis-translated/

	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			python3 $(genienlp) run-paraphrase $(default_translation_hparams) --temperature 0.4 --input_file ./$(experiment)/en/aug-en/unquoted-qpis-marian/$$f.tsv --output_file ./$(experiment)/marian/$*/unquoted-qpis-translated/$$f.tsv --model_name_or_path Helsinki-NLP/opus-mt-en-$*  ; \
		done ; \
	fi

$(experiment)/marian/%/unquoted-qpis-unrefined: $(foreach name, $(all_names), $(experiment)/marian/%/unquoted-qpis-translated/$(name))
	mkdir -p $@
	# insert programs (and context)
	for f in $(all_names) ; do \
		if [ $$f == $(train_name) ] ; then \
			paste <(awk '{for(i=0;i<$(train_output_per_example);i++)print}' ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv) <(cut -f2 ./$(experiment)/marian/$*/unquoted-qpis-translated/$$f.tsv)  <(awk '{for(i=0;i<$(train_output_per_example);i++)print}' ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv)  >  $@/$$f.tsv.tmp ; \
		else \
			paste <(awk '{for(i=0;i<$(evaltest_output_per_example);i++)print}' ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv) <(cut -f2 ./$(experiment)/marian/$*/unquoted-qpis-translated/$$f.tsv)  <(awk '{for(i=0;i<$(evaltest_output_per_example);i++)print}' ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv)  >  $@/$$f.tsv.tmp ; \
		fi ; \
	done

	# refine sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --refine_sentence --post_process_translation --num_columns $(num_columns) --input_file $@/$$f.tsv.tmp --output_file $@/$$f.tsv ; done

	rm -rf $@/*.tsv.tmp


$(experiment)/marian/%/unquoted-qpis: $(experiment)/marian/%/unquoted-qpis-unrefined
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --insert_space_quotes --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/marian/%/unquoted: $(experiment)/marian/%/unquoted-qpis
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/marian/%/quoted: $(experiment)/marian/%/unquoted
	mkdir -p $@
	# requote dataset (if successful, verifies parameters match in the sentence and in the program) (collect errors in a separate file)
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] || [ $$f == "train_missed_qa" ] ); then \
			$(genie) requote --skip-errors $(contextual) --mode replace $(handle-heuristics) --output-errors $@/"$$f"_errors.tsv -o $@/$$f.tsv $</$$f.tsv ; \
		else \
			$(genie) requote $(contextual)  --mode replace $(handle-heuristics) --output-errors $@/"$$f"_errors.tsv -o $@/$$f.tsv $</$$f.tsv ; \
		fi ; \
	done


$(experiment)/marian/%/augmented: $(experiment)/marian/%/quoted
	mkdir -p $@
	echo "Number of lines survived so far! :"
	for f in $(all_names) ; do echo "$$f" ; wc -l $(experiment)/marian/$*/quoted/$$f.tsv ; done
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_train_hparams) $</$$f.tsv ; \
		else \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_evaltest_hparams) $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/marian/%/final-qpis: $(experiment)/marian/%/augmented
	mkdir -p $@
	# qpis dataset
	for f in $(all_names) ; do $(genie) requote --mode qpis $(handle-heuristics) $(contextual) -o $@/$$f.tsv  $</$$f.tsv  ; done

$(experiment)/marian/%/final-cjkspaced: $(experiment)/marian/%/final-qpis
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/marian/%/final: $(experiment)/marian/%/final-cjkspaced
	mkdir -p $@
	# remove cjk spaces
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --num_columns $(num_columns) --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done

translate_marian_unquoted_%: $(experiment)/marian/%/final $(experiment)/marian/%/final-qpis
	# done!
	echo $@

translate_marian_unquoted_all_langs:
	for lang in $(marian_oht_languages) ; do \
		make translate_marian_unquoted_$$lang ; \
	done
