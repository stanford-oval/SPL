####################################################################################################################
##### back translate quoted dataset using GT  ###########################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/gt/quoted/$(name).txt)

# with no glossary option we will get output for both glossary and non-glossary translations
# so we use no_glossary only when downloading and post_processing the results
no_glossary ?= --no_glossary
skip_translation ?= false

$(foreach name, $(all_names), $(experiment)/oht/%/gt/quoted/$(name)):
	mkdir -p $(experiment)/oht/$*/gt/quoted
	# prepare quoted data for back translation to English
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_gt --input_file $(experiment)/oht/$*/quoted/$$f.tsv --output_file ./$(experiment)/oht/$*/gt/quoted/$$f.tsv.tmp ; done

	for f in $(all_names) ; do cut -f1,2 ./$(experiment)/oht/$*/gt/quoted/$$f.tsv.tmp > ./$(experiment)/oht/$*/gt/quoted/$$f.tsv ; rm -rf ./$(experiment)/oht/$*/gt/quoted/$$f.tsv.tmp ; done


$(experiment)/oht/%/gt/quoted-back: $(foreach name, $(all_names), $(experiment)/oht/%/gt/quoted/$(name))
	mkdir -p $@

	# upload dataset
	python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 --update_dataset --input_local_path $(experiment)/oht/$*/gt/quoted --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket)

 	# upload glossary
	if ! $(skip_translation) ; then \
		python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 --update_glossary --glossary_bucket $(glossary_bucket) --input_local_path $(experiment)/oht/$*/gt/quoted --input_names $(foreach name, $(all_names), $(name).tsv) --glossary_type ${glossary_type} --glossary_local_path $(multilingual_scripts)/extras/ --source_lang $* --target_langs en ; \
	fi

	# batch translate
	# you can specify multiple files to be translated simultaneously but we translate each split individually to keep output_buckets separate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
							--do_translate --input_local_path $(experiment)/oht/$*/gt/quoted --input_names $$f.tsv --output_bucket output_$(experiment)_$*_back_$$f --overwrite_output --glossary_type default \
								 --input_bucket $(input_bucket) --source_lang $* --target_langs en ; \
		done ; \
	fi

	# download and post_process results
	for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 						--no_glossary --download_results --input_local_path $(experiment)/oht/$*/gt/quoted --input_names $$f.tsv --output_bucket output_$(experiment)_$*_back_$$f --overwrite_output --glossary_type default \
							 $(no_glossary) --input_bucket $(input_bucket) --source_lang $* --target_langs en --output_local_path $@ ; \
	done


$(experiment)/oht/%/gt/quoted-unrefined-back: $(experiment)/oht/%/gt/quoted-back
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do  paste $<$$f.tsv $(experiment)/en/quoted-uniq-progs/$$f.tsv >  $@/$$f.tsv ; done


$(experiment)/oht/%/gt/quoted-back-cleaned: $(experiment)/oht/%/gt/quoted-unrefined-back
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/gt/quoted-back-augmented: $(experiment)/oht/%/gt/quoted-back-cleaned
	mkdir -p $@
	# augment (=unquote) qpis inputs with actual parameter values

	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale en -l en-US $(default_augment_train_hparams)   $</$$f.tsv  ; \
		else \
			$(genie) augment -o $@/$$f.tsv  --param-locale en -l en-US $(default_augment_evaltest_hparams)  $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/oht/%/gt/final-back: $(experiment)/oht/%/gt/quoted-back-augmented
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


back_translate_gt_quoted_%: $(experiment)/oht/%/gt/final-back
	# done!
	echo $@


back_translate_gt_quoted_all_langs:
	for lang in $(gt_oht_languages) ; do \
		make -B back_translate_gt_quoted_$$lang ; \
	done
