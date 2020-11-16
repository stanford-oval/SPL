####################################################################################################################
##### process oht data #####################################################################################
####################################################################################################################
.PRECIOUS: $(foreach name, $(all_names), $(experiment)/oht/%/input/$(name).txt)


$(foreach name, $(all_names), $(experiment)/oht/%/input/$(name).txt):
	mkdir -p $(experiment)/oht/$*/input/

	# process old oht
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --process_oht --input_delimiter "(?<=\d)\.\s+" --num_columns 2 --input_file $(dataset_folder)/old_merged/$*/$(experiment)_num_"$$f"_"$*"-merged.txt --output_file $(experiment)/oht/$*/input/$$f.txt.old ; done

	# process new oht and merge for test set
	for f in $(all_names) ; do \
		if ( [ $$f == $(test_name) ] ) ; then \
			python3 $(multilingual_scripts)/text_edit.py --process_oht --num_columns 2 --input_file $(dataset_folder)/new_merged/$*/$(experiment)_"$$f"_"$*"_merged.txt --output_file $(experiment)/oht/$*/input/$$f.txt.new ; \
			cat $(experiment)/oht/$*/input/$$f.txt.old  $(experiment)/oht/$*/input/$$f.txt.new > $(experiment)/oht/$*/input/$$f.txt ; \
			rm -rf $(experiment)/oht/$*/input/$$f.txt.old  $(experiment)/oht/$*/input/$$f.txt.new ; \
		elif ( [ $$f == $(eval_name) ] ) ; then \
			cat $(experiment)/oht/$*/input/$$f.txt.old > $(experiment)/oht/$*/input/$$f.txt ; \
			rm -rf $(experiment)/oht/$*/input/$$f.txt.old ; \
		fi ; \
	done

$(experiment)/oht/%/unquoted-qpis-oht: $(foreach name, $(all_names), $(experiment)/oht/%/input/$(name).txt)
	mkdir -p $@
	# match ids with ref eval
	for f in $(all_names) ; do \
		if ( [ $$f == $(test_name) ] ) ; then \
			python3 $(multilingual_scripts)/text_edit.py --match_ids --num_columns 2  --add_token "" --input_file ./$(experiment)/oht/$*/input/$$f.txt --ref_file $(experiment)/en/input/$$f.tsv --output_file $@/$$f.tsv ; \
		elif ( [ $$f == $(eval_name) ] ) ; then \
			head -n $(eval_$(experiment)_oht_size) $(experiment)/en/input/$$f.tsv > $(experiment)/en/input/$$f.tsv.ref ; \
			python3 $(multilingual_scripts)/text_edit.py --match_ids --num_columns 2  --add_token "" --input_file ./$(experiment)/oht/$*/input/$$f.txt --ref_file $(experiment)/en/input/$$f.tsv.ref --output_file $@/$$f.tsv ; \
		fi ; \
	done


$(experiment)/oht/%/unquoted-qpis-unrefined: $(experiment)/oht/%/unquoted-qpis-oht
	mkdir -p $@
	# insert programs
	for f in $(all_names) ; do \
		if ( [ $$f == $(test_name) ] ) ; then \
			cut -f3 $(experiment)/en/input/$$f.tsv | paste $</$$f.tsv - >  $@/$$f.tsv ; \
		elif ( [ $$f == $(eval_name) ] ) ; then \
			cut -f3 $(experiment)/en/input/$$f.tsv.ref | paste $</$$f.tsv - >  $@/$$f.tsv ; \
			if [ -s $(experiment)/marian/$*/final-cjkspaced/$$f.tsv ] ; then \
				tail -n +$(shell echo $$(( $(eval_$(experiment)_oht_size) + 1))) $(experiment)/marian/$*/final-cjkspaced/eval.tsv >> $@/$$f.tsv ; \
			else \
				tail -n +$(shell echo $$(( $(eval_$(experiment)_oht_size) + 1))) $(experiment)/gt/$*/final-cjkspaced/eval.tsv >> $@/$$f.tsv ; \
			fi ; \
			rm -rf $(experiment)/en/input/$$f.tsv.ref ; \
		fi ; \
	done


$(experiment)/oht/%/unquoted-qpis-cleaned: $(experiment)/oht/%/unquoted-qpis-unrefined
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --insert_space_quotes --refine_sentence --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/oht/%/unquoted-qpis: $(experiment)/oht/%/unquoted-qpis-cleaned
	mkdir -p $@
	# with new approach the program params will match sentence params since we prevented parameters from being translated
	for f in $(all_names) ; do cp $</$$f.tsv $@/$$f.tsv ; done

$(experiment)/oht/%/unquoted: $(experiment)/oht/%/unquoted-qpis
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/oht/%/quoted: $(experiment)/oht/%/unquoted
	mkdir -p $@
	# requote dataset (if successful, verifies parameters match in the sentence and in the program) (skip errors only for train)
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) requote --skip-errors --mode replace -o $@/$$f.tsv $</$$f.tsv ; \
		else \
			$(genie) requote --mode replace -o $@/$$f.tsv $<$$f.tsv ; \
		fi ; \
	done


$(experiment)/oht/%/augmented: $(experiment)/oht/%/quoted
	mkdir -p $@
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l $* $(default_augment_train_hparams)  $</$$f.tsv  ; \
		else \
			$(genie) augment -o $@/$$f.tsv  --param-locale $* -l $* $(default_augment_evaltest_hparams)  $</$$f.tsv  ; \
		fi ; \
	done

$(experiment)/oht/%/final-qpis: $(experiment)/oht/%/augmented
	mkdir -p $@
	# qpis dataset
	for f in $(all_names) ; do $(genie) requote --mode qpis -o $@/$$f.tsv  $</$$f.tsv  ; done


$(experiment)/oht/%/final-qpis-cjkfixed: $(experiment)/oht/%/final-qpis
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


$(experiment)/oht/%/final: $(experiment)/oht/%/final-qpis-cjkfixed
	mkdir -p $@
	# remove qpis
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


process_oht_%: $(experiment)/oht/%/final $(experiment)/oht/%/final-qpis
	# done!
	echo $@

process_oht_all_langs:
	for lang in $(oht_languages) ; do \
		make -B process_oht_$$lang ; \
	done
