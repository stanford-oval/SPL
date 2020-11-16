####################################################################################################################
##### direct translate with Marian #####################################################################################
####################################################################################################################

$(experiment)/marian/%/unquoted-qpis-direct-translated:
	mkdir -p $@

	if ! $(skip_translation) ; then \
		for f in $(all_names) ; do \
			python3 $(genienlp) run-paraphrase $(default_translation_hparams) --temperature 0.4 --input_file ./$(experiment)/en/aug-en/unquoted-qpis-marian/$$f.tsv --output_file $@/$$f.tsv --model_name_or_path Helsinki-NLP/opus-mt-en-$* ; \
		done ; \
	fi

$(experiment)/marian/%/unquoted-qpis-unrefined-direct: $(experiment)/marian/%/unquoted-qpis-direct-translated
	mkdir -p $@
	# insert programs (and context)
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f2 $</$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv ./$(experiment)/en/aug-en/unquoted-qpis-contexts/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv ; done ; \
	else \
		for f in $(all_names) ; do cut -f2 $</$$f.tsv | paste ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv - ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv >  $@/$$f.tsv ; done ; \
	fi

$(experiment)/marian/%/unquoted-qpis-cleaned-direct: $(experiment)/marian/%/unquoted-qpis-unrefined-direct
	mkdir -p $@
	# fix punctuation and clean dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --insert_space_quotes --refine_sentence --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done

$(experiment)/marian/%/unquoted-qpis-direct: $(experiment)/marian/%/unquoted-qpis-cleaned-direct
	mkdir -p $@
	for f in $(all_names) ; do cp $</$$f.tsv $@/$$f.tsv ; done

$(experiment)/marian/%/final-direct: $(experiment)/marian/%/unquoted-qpis-direct
	mkdir -p $@
	# remove quotation marks in the sentence
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --fix_spaces_cjk --param_language $* --remove_qpis --input_file $</$$f.tsv  --output_file $@/$$f.tsv  ; done


translate_marian_direct_%: $(experiment)/marian/%/final-direct
	# done!
	echo $@

translate_marian_direct_all_langs:
	for lang in $(marian_boot_languages) ; do \
		make -B translate_marian_direct_$$lang ; \
	done
