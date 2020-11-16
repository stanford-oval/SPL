####################################################################################################################
##### translate unquoted data using GT #####################################################################################
####################################################################################################################
skip_translation=false

$(foreach name, $(all_names), $(experiment)/gt/%/unquoted-qpis-translated/$(name)): $(experiment)/en/aug-en/unquoted-qpis-translated/
	mkdir -p $(experiment)/gt/$*/unquoted-qpis-translated/

	# upload dataset
	python3 $(multilingual_scripts)/translate_v3.py --update_dataset --input_local_path $< --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket)

 	# upload glossary
	python3 $(multilingual_scripts)/translate_v3.py --update_glossary --glossary_bucket $(glossary_bucket) --input_local_path $< --input_names $(foreach name, $(all_names), $(name).tsv) --glossary_type ${glossary_type} --glossary_local_path $(multilingual_scripts)/extras/ --source_lang en --target_langs $*

	# batch translate
	# you can specify multiple files to be translated simultaneously but we translate each split individually to keep output_buckets separate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --do_translate --input_local_path $< --input_names $$f.tsv --output_bucket output_$(experiment)_$*_$$f --overwrite_output --glossary_type default \
								 --input_bucket $(input_bucket) --source_lang en --target_langs $* ; \
		done ; \
	fi

	# download and post_process results
	for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --download_results --input_local_path $< --input_names $$f.tsv --output_bucket output_$(experiment)_$*_$$f --overwrite_output --glossary_type default \
							 --input_bucket $(input_bucket) --source_lang en --target_langs $* --output_local_path ./$(experiment)/gt/$*/unquoted-qpis-translated/ ; \
	done

$(experiment)/gt/%/unquoted-qpis-unrefined: $(foreach name, $(all_names), $(experiment)/gt/%/unquoted-qpis-translated/$(name))
	mkdir -p $@
	# insert programs (and context)
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f2 ./$(experiment)/gt/$*/unquoted-qpis-translated/$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv ./$(experiment)/en/aug-en/unquoted-qpis-contexts/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv.tmp ; done ; \
	else \
		for f in $(all_names) ; do cut -f2 ./$(experiment)/gt/$*/unquoted-qpis-translated/$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv.tmp ; done ; \
	fi

	# refine sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --num_columns $(num_columns) --input_file $@/$$f.tsv.tmp --output_file $@/$$f.tsv ; done

	rm -rf $@/*.tsv.tmp

$(experiment)/gt/%/unquoted-qpis-cleaned: $(experiment)/gt/%/unquoted-qpis-unrefined
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --insert_space_quotes --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/gt/%/unquoted-qpis: $(experiment)/gt/%/unquoted-qpis-cleaned
	mkdir -p $@
	# with glossary approach the program params will match sentence params since we prevented parameters from being translated
	for f in $(all_names) ; do cp $</$$f.tsv $@/$$f.tsv ; done

$(experiment)/gt/%/unquoted: $(experiment)/gt/%/unquoted-qpis
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/gt/%/quoted: $(experiment)/gt/%/unquoted
	mkdir -p $@
	# requote dataset (if successful, verifies parameters match in the sentence and in the program) (skip errors only for train)
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ]); then \
			$(genie) requote --skip-errors $(contextual) $(handle-heuristics) --mode replace --output-errors $@"$$f"_errors.tsv -o $@/$$f.tsv $</$$f.tsv ; \
		else \
			$(genie) requote --mode replace $(contextual) $(handle-heuristics) --output-errors $@/"$$f"_errors.tsv -o $@/$$f.tsv $</$$f.tsv ; \
		fi ; \
	done

num_attempts = 10000
$(experiment)/gt/%/augmented: $(experiment)/gt/%/quoted
	mkdir -p $@
	echo "Number of lines survived so far! :"
	for f in $(all_names) ; do echo "$$f" ; wc -l $(experiment)/gt/$*/quoted/$$f.tsv ; done
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_train_hparams) $</$$f.tsv ; \
		else \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_evaltest_hparams) $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/gt/%/final-qpis: $(experiment)/gt/%/augmented
	mkdir -p $@
	# qpis dataset
	for f in $(all_names) ; do $(genie) requote --mode qpis $(handle-heuristics) $(contextual) -o $@/$$f.tsv $</$$f.tsv  ; done


$(experiment)/gt/%/final: $(experiment)/gt/%/final-qpis
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done



translate_gt_unquoted_%: $(experiment)/gt/%/final $(experiment)/gt/%/final-qpis

	# done!
	echo $@

translate_gt_unquoted_all_langs:
	for lang in $(gt_oht_languages) ; do \
		make translate_gt_unquoted_$$lang ; \
	done
