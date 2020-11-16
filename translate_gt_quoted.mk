####################################################################################################################
##### translate quoted dataset with GT  ######################################################################
####################################################################################################################
# with no glossary option we will get output for both glossary and non-glossary translations
# so we use no_glossary only when downloading and post_processing the results
no_glossary ?= --no_glossary
skip_translation ?= false

$(experiment)/gt/%/quoted-uniq-translated:
	mkdir -p $@
	# upload dataset
	if ! $(skip_translation) ; then \
		python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 --update_dataset --input_local_path $(experiment)/en/quoted-uniq-gt --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket) ; \
	fi

	# upload glossary for quoted data
	if ! $(skip_translation) ; then \
		python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 --update_glossary --no_translate_params --glossary_bucket $(glossary_bucket)  --input_local_path ./$(experiment)/en/quoted-uniq --input_names $(foreach name, $(all_names), $(name).tsv) --glossary_type ${glossary_type} --glossary_local_path $(multilingual_scripts)/extras/ --source_lang en --target_langs $* ; \
	fi

	# batch translate
	# you can specify multiple files to be translated simultaneously but we translate each split individually to keep output_buckets separate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 --do_translate --input_local_path ./$(experiment)/en/quoted-uniq-gt --input_names $$f.tsv --output_bucket output_$(experiment)_$*_quoted_$$f --overwrite_output --glossary_type default \
								 --input_bucket $(input_bucket) --source_lang en --target_langs $* ; \
		done ; \
	fi

	# download and post_process results
	for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 --download_results $(no_glossary) --input_local_path ./$(experiment)/en/quoted-uniq-gt --input_names $$f.tsv --output_bucket output_$(experiment)_$*_quoted_$$f --overwrite_output --glossary_type default \
							 --input_bucket $(input_bucket) --source_lang en --target_langs $* --output_local_path ./$(experiment)/gt/$*/quoted-uniq-translated/ ; \
	done

$(experiment)/gt/%/final-quoted: $(experiment)/gt/%/quoted-uniq-translated
	mkdir -p $@
	# insert programs (and context)
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f2 ./$(experiment)/gt/$*/quoted-uniq-translated/$$f.tsv | paste ./$(experiment)/en/quoted-uniq-ids/$$f.tsv ./$(experiment)/en/quoted-uniq-contexts/$$f.tsv -  ./$(experiment)/en/quoted-uniq-progs/$$f.tsv  >  $(experiment)/gt/$*/final-quoted/$$f.tsv.tmp ; done ; \
	else \
		for f in $(all_names) ; do cut -f2 ./$(experiment)/gt/$*/quoted-uniq-translated/$$f.tsv | paste ./$(experiment)/en/quoted-uniq-ids/$$f.tsv -  ./$(experiment)/en/quoted-uniq-progs/$$f.tsv  >  $(experiment)/gt/$*/final-quoted/$$f.tsv.tmp ; done ; \
	fi

	# refine sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --refine_sentence --post_process_translation --num_columns $(num_columns) --input_file $(experiment)/gt/$*/final-quoted/$$f.tsv.tmp --output_file $(experiment)/gt/$*/final-quoted/$$f.tsv ; done

	rm -rf $(experiment)/gt/$*/final-quoted/*.tsv.tmp



$(experiment)/gt/%/final-quoted-augmented-unrefined: $(experiment)/gt/%/final-quoted
	mkdir -p $@
	# augment (=unquote) qpis inputs with actual parameter values

	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_train_hparams) $</$$f.tsv ; \
		else \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_evaltest_hparams) $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/gt/%/final-cjkspaced: $(experiment)/gt/%/final-quoted-augmented-unrefined
	mkdir -p $@
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py  --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done

$(experiment)/gt/%/final: $(experiment)/gt/%/final-cjkspaced
	mkdir -p $@
	# remove cjk spaces
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done



translate_gt_quoted_%: $(experiment)/gt/%/final
	# done!
	echo $@

translate_gt_quoted_all_langs:
	for lang in $(gt_oht_languages) ; do \
		make translate_gt_quoted_$$lang ; \
	done
