####################################################################################################################
##### direct translate with GT #####################################################################################
####################################################################################################################

$(experiment)/gt/%/unquoted-qpis-direct-translated:
	mkdir -p $@

	if ! $(skip_translation) ; then \
		python3 $(multilingual_scripts)/translate_v3.py  --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) --update_dataset --input_local_path ./$(experiment)/en/aug-en/unquoted-qpis-gt/ --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket) ; \
		for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py  --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
		 						--do_translate --no_glossary --input_local_path ./$(experiment)/en/aug-en/unquoted-qpis-gt/ --input_names $$f.tsv --output_bucket output_$(experiment)_$*_just_$$f --overwrite_output \
								 --input_bucket $(input_bucket) --source_lang en --target_langs $* ; \
		done ; \
	fi

	for f in $(all_names) ; do python3 $(multilingual_scripts)/translate_v3.py  --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 						--download_results --no_glossary --input_local_path ./$(experiment)/en/aug-en/unquoted-qpis-marian/ --input_names $$f.tsv --output_bucket output_$(experiment)_$*_just_$$f --overwrite_output --glossary_type default \
							 --input_bucket ../$(experiment)/en/aug-en/unquoted-qpis-gt/ --source_lang en --target_langs $* --output_local_path $@ ; \
	done ; \

$(experiment)/gt/%/unquoted-qpis-unrefined-direct: $(experiment)/gt/%/unquoted-qpis-direct-translated
	mkdir -p $@
	# insert programs (and context)
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f2 $</$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv ./$(experiment)/en/aug-en/unquoted-qpis-contexts/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv ; done ; \
	else \
		for f in $(all_names) ; do cut -f2 $</$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv ; done ; \
	fi


$(experiment)/gt/%/unquoted-qpis-cleaned-direct: $(experiment)/gt/%/unquoted-qpis-unrefined-direct
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --insert_space_quotes --refine_sentence --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done

$(experiment)/gt/%/unquoted-qpis-direct: $(experiment)/gt/%/unquoted-qpis-cleaned-direct
	mkdir -p $@
	for f in $(all_names) ; do cp $</$$f.tsv ./$(experiment)/gt/$*/unquoted-qpis-direct/$$f.tsv ; done

$(experiment)/gt/%/final-direct: $(experiment)/gt/%/unquoted-qpis-direct
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done



translate_gt_direct_%: $(experiment)/gt/%/final-direct

	# done!
	echo $@

translate_gt_direct_all_langs:
	for lang in $(gt_boot_languages) ; do \
		make -B translate_gt_direct_$$lang ; \
	done