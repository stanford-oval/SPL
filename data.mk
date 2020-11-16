
$(experiment)/en/input: $(dataset_folder)/$(experiment)
	mkdir -p $@

	# replace_ids for train set if original splits do not have unique ids
	for f in $(all_names) ; do \
		if ( $(replace_ids) && ! [ $$f == $(train_name) ] ); then \
			python3 $(multilingual_scripts)/text_edit.py --replace_ids --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; \
		elif ( $(preprocess_paraphrased) && [ $$f == $(train_name) ] ); then \
			python3 $(multilingual_scripts)/text_edit.py --preprocess_paraphrased --num_columns $(num_columns) --input_file <$/$$f.tsv --output_file $@/$$f.tsv ; \
		else \
			cp $</$$f.tsv $@/$$f.tsv ; \
		fi ; \
	done

$(experiment)/en/input-qpis: $(experiment)/en/input
	mkdir -p $@

	# qpis input data
	for f in $(all_names) ; do $(genie) requote --mode qpis --skip-errors $(handle-heuristics) $(contextual) -o $@/$$f.tsv $</$$f.tsv ; done


$(experiment)/en/quoted-qpis: $(experiment)/en/input-qpis
	mkdir -p $@
	# requote the input qpis data
	for f in $(all_names) ; do $(genie) requote --skip-errors $(handle-heuristics) $(contextual) --mode replace -o $@/$$f.tsv $</$$f.tsv ; done


$(experiment)/en/quoted: $(experiment)/en/quoted-qpis
	mkdir -p $@
	# remove qpis from quoted dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/en/quoted-uniq: $(experiment)/en/quoted
	mkdir -p $@
	# find unique sentences for train set if necessary
	for f in $(all_names) ; do \
		if ( $(remove_duplicate_sents) && [ $$f == $(train_name) ] ) ; then \
			python3 $(multilingual_scripts)/text_edit.py --remove_duplicate_sents --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; \
		else \
			cp $</$$f.tsv $@/$$f.tsv; \
		fi ; \
	done

$(experiment)/en/quoted-uniq-qpis: $(experiment)/en/quoted-qpis
	mkdir -p $@
	# find unique sentences for train set if necessary
	for f in $(all_names) ; do \
		if ( $(remove_duplicate_sents) && [ $$f == $(train_name) ] ) ; then \
			python3 $(multilingual_scripts)/text_edit.py --remove_duplicate_sents --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; \
		else \
			cp $</$$f.tsv $@/$$f.tsv; \
		fi ; \
	done

$(experiment)/en/aug-%/unquoted-qpis: $(experiment)/en/quoted-uniq-qpis
	# augment (=unquote) qpis inputs with actual parameter values
	mkdir -p $@
	# augment dataset in target language
	for f in $(all_names) ; do \
		if ( [ $$f == $(train_name) ] ); then \
			$(genie) augment -o $@/$$f.tsv --param-locale $* -l en $(default_augment_train_hparams) \
			--synthetic-expand-factor 1 --quoted-paraphrasing-expand-factor 1 --no-quote-paraphrasing-expand-factor 1 \
			 $</$$f.tsv  ; \
		else \
			$(genie) augment -o $@/$$f.tsv  --param-locale $* -l en $(default_augment_evaltest_hparams)  $</$$f.tsv  ; \
		fi ; \
	done


########################
$(experiment)/en/aug-%/unquoted-qpis/$(train_name)_blowup.tsv: $(experiment)/en/quoted-uniq-qpis/$(train_name).tsv
	# augment (=unquote) qpis inputs with actual parameter values with blowup
	$(genie) augment -o $@ --param-locale $* -l en $(default_augment_train_hparams)  $<

$(experiment)/en/aug-%/unquoted/$(train_name)_blowup.tsv: $(experiment)/en/aug-%/unquoted-qpis/$(train_name)_blowup.tsv
	# remove qpis from unquoted data
	python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $< --output_file $@

########################

$(experiment)/en/aug-%/unquoted: $(experiment)/en/aug-%/unquoted-qpis
	mkdir -p $@
	# remove qpis from unquoted data
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/en/quoted-uniq-ids/ $(experiment)/en/quoted-uniq-contexts/ $(experiment)/en/quoted-uniq-sents/ $(experiment)/en/quoted-uniq-progs/: $(experiment)/en/quoted-uniq/
	mkdir -p $(experiment)/en/quoted-uniq-ids/ $(experiment)/en/quoted-uniq-contexts/ $(experiment)/en/quoted-uniq-sents/ $(experiment)/en/quoted-uniq-progs/
	# create id, (context,) sentence, program splits for quoted data
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f1 $</$$f.tsv  > ./$(experiment)/en/quoted-uniq-ids/$$f.tsv ; \
								   cut -f2 $</$$f.tsv > ./$(experiment)/en/quoted-uniq-contexts/$$f.tsv ; \
								   cut -f3 $</$$f.tsv > ./$(experiment)/en/quoted-uniq-sents/$$f.tsv ; \
								   cut -f4- $</$$f.tsv > ./$(experiment)/en/quoted-uniq-progs/$$f.tsv ; \
								done ; \
	else \
		for f in $(all_names) ; do cut -f1 $</$$f.tsv  > ./$(experiment)/en/quoted-uniq-ids/$$f.tsv ; \
								   cut -f2 $</$$f.tsv > ./$(experiment)/en/quoted-uniq-sents/$$f.tsv ; \
								   cut -f3- $</$$f.tsv > ./$(experiment)/en/quoted-uniq-progs/$$f.tsv ; \
								done ; \
	fi

$(experiment)/en/aug-en/unquoted-qpis-ids/ $(experiment)/en/aug-en/unquoted-qpis-contexts/ $(experiment)/en/aug-en/unquoted-qpis-sents/ $(experiment)/en/aug-en/unquoted-qpis-progs/: $(experiment)/en/aug-en/unquoted-qpis/
	mkdir -p $(experiment)/en/aug-en/unquoted-qpis-ids/ $(experiment)/en/aug-en/unquoted-qpis-contexts/ $(experiment)/en/aug-en/unquoted-qpis-sents/ $(experiment)/en/aug-en/unquoted-qpis-progs/
	# create id, (context,) sentence, program splits for unquoted data
	if [ ! -z $(contextual) ] ; then \
		for f in $(all_names) ; do cut -f1 $</$$f.tsv  > ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv ; \
								   cut -f2 $</$$f.tsv > ./$(experiment)/en/aug-en/unquoted-qpis-contexts/$$f.tsv ; \
								   cut -f3 $</$$f.tsv > ./$(experiment)/en/aug-en/unquoted-qpis-sents/$$f.tsv ; \
								   cut -f4- $</$$f.tsv > ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv ; \
								done ; \
	else \
		for f in $(all_names) ; do cut -f1 $</$$f.tsv  > ./$(experiment)/en/aug-en/unquoted-qpis-ids/$$f.tsv ; \
								   cut -f2 $</$$f.tsv > ./$(experiment)/en/aug-en/unquoted-qpis-sents/$$f.tsv ; \
								   cut -f3- $</$$f.tsv > ./$(experiment)/en/aug-en/unquoted-qpis-progs/$$f.tsv ; \
								done ; \
	fi


$(experiment)/en/quoted-uniq-gt: $(experiment)/en/quoted-uniq $(experiment)/en/aug-en/unquoted-qpis-ids/ $(experiment)/en/aug-en/unquoted-qpis-sents/ $(experiment)/en/aug-en/unquoted-qpis-progs/ $(experiment)/en/quoted-uniq-ids/ $(experiment)/en/quoted-uniq-sents/ $(experiment)/en/quoted-uniq-progs/
	mkdir -p $@
	# prepare quoted data for google translation
	mkdir -p ./$(experiment)/en/quoted-uniq-gt-tmp
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_gt --replace_ids --num_columns $(num_columns) --input_file $</$$f.tsv --output_file ./$(experiment)/en/quoted-uniq-gt-tmp/$$f.tsv ; cut -f1,$(if $(contextual),3,2) ./$(experiment)/en/quoted-uniq-gt-tmp/$$f.tsv > $@/$$f.tsv ; done
	rm -rf ./$(experiment)/en/quoted-uniq-gt-tmp

$(experiment)/en/aug-%/unquoted-qpis-gt: $(experiment)/en/aug-%/unquoted-qpis
	mkdir -p $@
	# prepare unquoted data for google translation
	mkdir -p ./$(experiment)/en/aug-$*/unquoted-qpis-gt-tmp
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_gt --replace_ids --num_columns $(num_columns) --input_file $</$$f.tsv --output_file ./$(experiment)/en/aug-$*/unquoted-qpis-gt-tmp/$$f.tsv ; cut -f1,$(if $(contextual),3,2) ./$(experiment)/en/aug-$*/unquoted-qpis-gt-tmp/$$f.tsv > $@/$$f.tsv ; done
	rm -rf ./$(experiment)/en/aug-$*/unquoted-qpis-gt-tmp

$(experiment)/en/quoted-uniq-marian:
	mkdir -p $@
	mkdir -p $(experiment)/en/quoted-uniq-marian-tmp
	# prepare quoted data for marian translation
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_marian --replace_ids  --num_columns $(num_columns) --input_file $(experiment)/en/quoted-uniq/$$f.tsv --output_file $(experiment)/en/quoted-uniq-marian-tmp/$$f.tsv ; cut -f1,$(if $(contextual),3,2) $(experiment)/en/quoted-uniq-marian-tmp/$$f.tsv > $@/$$f.tsv ; done
	rm -rf $(experiment)/en/quoted-uniq-marian-tmp

$(experiment)/en/aug-%/unquoted-qpis-marian:
	mkdir -p $@
	mkdir -p $(experiment)/en/aug-$*/unquoted-qpis-marian-tmp
	# prepare unquoted data for marian translation
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --prepare_for_marian --replace_ids  --num_columns $(num_columns) --input_file $(experiment)/en/aug-en/unquoted-qpis/$$f.tsv --output_file $(experiment)/en/aug-$*/unquoted-qpis-marian-tmp/$$f.tsv ; cut -f1,$(if $(contextual),3,2) $(experiment)/en/aug-$*/unquoted-qpis-marian-tmp/$$f.tsv > $@/$$f.tsv ; done
	rm -rf $(experiment)/en/aug-$*/unquoted-qpis-marian-tmp


$(experiment)/en/aug-%/unquoted: $(experiment)/en/aug-%/unquoted-qpis
	mkdir -p $@
	# remove qpis from unquoted dataset
	for f in $(all_names) ; do python3 $(multilingual_scripts)/text_edit.py --remove_qpis --num_columns $(num_columns) --input_file $</$$f.tsv --output_file $@/$$f.tsv ; done


$(experiment)/data_en_aug_%: $(experiment)/en/aug-%/unquoted-qpis-gt $(experiment)/en/quoted-uniq-gt $(experiment)/en/aug-%/unquoted $(experiment)/en/quoted-uniq-marian $(experiment)/en/aug-%/unquoted-qpis-marian
	mkdir -p $(experiment)/en
	# done!
	echo $@

process_data:
	make experiment=$(experiment) $(experiment)/data_en_aug_en

process_train_blowup:
	make experiment=$(experiment) $(experiment)/en/aug-en/unquoted/$(train_name)_blowup.tsv
