####################################################################################################################
##### back translate direct dataset using GT  ###########################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/gt/direct/$(name).txt)

# with no glossary option we will get output for both glossary and non-glossary translations
# so we use no_glossary only when downloading and post_processing the results
no_glossary ?= --no_glossary
skip_translation ?= false

$(foreach name, $(all_names), $(experiment)/oht/%/gt/direct/$(name)):
	mkdir -p $(experiment)/oht/$*/gt/direct
	# prepare direct data for back translation to English
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_gt --input_file $(experiment)/oht/$*/final/$$f.tsv --output_file ./$(experiment)/oht/$*/gt/direct/$$f.tsv.tmp ; done

	for f in $(all_names) ; do cut -f1,2 ./$(experiment)/oht/$*/gt/direct/$$f.tsv.tmp > ./$(experiment)/oht/$*/gt/direct/$$f.tsv ; rm -rf ./$(experiment)/oht/$*/gt/direct/$$f.tsv.tmp ; done


$(experiment)/oht/%/gt/direct-back: $(foreach name, $(all_names), $(experiment)/oht/%/gt/direct/$(name))
	mkdir -p $@

	# upload dataset
	python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 --update_dataset --input_local_path $(experiment)/oht/$*/gt/direct --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket)

 	# upload glossary
	if ! $(skip_translation) ; then \
		python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 --update_glossary --glossary_bucket $(glossary_bucket) --input_local_path $(experiment)/oht/$*/gt/direct --input_names $(foreach name, $(all_names), $(name).tsv) --glossary_type ${glossary_type} --glossary_local_path $(multilingual_scripts)/extras/ --source_lang $* --target_langs en ; \
	fi

	# batch translate
	# you can specify multiple files to be translated simultaneously but we translate each split individually to keep output_buckets separate
	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
							--do_translate --input_local_path $(experiment)/oht/$*/gt/direct --input_names $$f.tsv --output_bucket output_$(experiment)_$*_back_$$f --overwrite_output --glossary_type default \
								 --input_bucket $(input_bucket) --source_lang $* --target_langs en ; \
		done ; \
	fi

	# download and post_process results
	for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 						--no_glossary --download_results --input_local_path $(experiment)/oht/$*/gt/direct --input_names $$f.tsv --output_bucket output_$(experiment)_$*_back_$$f --overwrite_output --glossary_type default \
							 $(no_glossary) --input_bucket $(input_bucket) --source_lang $* --target_langs en --output_local_path $@ ; \
	done


$(experiment)/oht/%/gt/direct-unrefined-back: $(experiment)/oht/%/gt/direct-back
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do cut -f3 $(experiment)/oht/$*/final/$$f.tsv | paste $(experiment)/oht/$*/gt/direct-back/$$f.tsv - >  $@/$$f.tsv ; done


$(experiment)/oht/%/gt/direct-back-cleaned: $(experiment)/oht/%/gt/direct-unrefined-back
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --post_process_translation --refine_sentence --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/gt/direct-final-back: $(experiment)/oht/%/gt/direct-back-cleaned
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


back_translate_gt_direct_%: $(experiment)/oht/%/gt/direct-final-back
	# done!
	echo $@


back_translate_gt_direct_all_langs:
	for lang in $(gt_oht_languages) ; do \
		make -B back_translate_gt_direct_$$lang ; \
	done
