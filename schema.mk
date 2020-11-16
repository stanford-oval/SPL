.PHONY: all syncup syncdown clean %_eval eval-all-% %_train train-all upload_data \
 upload_glossary batch_translate_% translate_%

skip_shared_param_download = true

shared-parameter-datasets.tsv:

	if ! $(skip_shared_param_download) ; then \
		$(thingpedia_cli) --url https://almond-dev.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key) --access-token invalid \
		  download-entity-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets ; \
		$(thingpedia_cli) --url https://almond.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key_2) --access-token invalid \
		  download-string-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets ; \
		$(thingpedia_cli) --url https://almond-dev.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key) --access-token invalid \
		  download-string-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets --type org.openstreetmap:restaurant ; \
		$(thingpedia_cli) --url https://almond-dev.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key) --access-token invalid \
		  download-string-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets --type org.openstreetmap:hotel ; \
		$(thingpedia_cli) --url https://almond-dev.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key) --access-token invalid \
		  download-string-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets --type com.spotify:genre ; \
		$(thingpedia_cli) --url https://almond-dev.stanford.edu/thingpedia --developer-key $(thingpedia_developer_key) --access-token invalid \
		  download-string-values --manifest $@.tmp --append-manifest -d shared-parameter-datasets --type tt:book_name ; \
		echo "entity	tt:us_state	shared-parameter-datasets/org.schema:us_state.json" >> $@.tmp ; \
	fi

	for lang in $(oht_languages_plus_en) ; do \
		cat $@.tmp | sort | uniq | gsed -r "s|^(\w*)\t|\1\t$$lang\t|g"   >> $@ ; \
	done

	rm -rf $@.tmp


$(experiment)/parameter-datasets.tsv: $(foreach lang, $(oht_languages_plus_en), $(multilingual_scripts)/../schema_data_processed/$(experiment)/$(lang)/data.json) $(experiment)/schema.tt   shared-parameter-datasets.tsv

	# insert shared parameters mapping first
	gsed "s|\tshared-parameter-datasets|\t../shared-parameter-datasets|g" shared-parameter-datasets.tsv | sort | uniq > $@ ; \

	for lang in $(oht_languages_plus_en) ; do \
		rm -rf $(experiment)/parameter-datasets-$$lang ; \
		$(genie) make-string-datasets --dataset schemaorg -l $$lang --manifest $@ --append-manifest -d $(experiment)/parameter-datasets-$$lang --thingpedia $(experiment)/schema.trimmed.tt --data $(multilingual_scripts)/../schema_data_processed/$(experiment)/$$lang/data.json --class-name $($(experiment)_class_name) ; \
 		for missing_val in $(missing_tsv_values) ; do \
			echo "string	$$lang	$$missing_val	../shared-parameter-datasets/$$missing_val.tsv" >> $@ ; \
			if [ ! -s ./shared-parameter-datasets/$$missing_val.tsv ] ; then \
				cp ./shared-parameter-datasets-en/$$missing_val.tsv ./shared-parameter-datasets/ ; \
			fi ; \
		done ; \
		python3 $(multilingual_scripts)/adjust_parameter_files.py $(experiment)/parameter-datasets-$$lang $(experiment) ; \
	done

	for lang in $(missing_manifest_languages) ; do \
		for missing_val in $(missing_manifest_entities) ; do \
			echo "entity	$$lang	$$missing_val	parameter-datasets-$$lang/$$missing_val.json" >> $@ ; \
		done ; \
		for missing_val in $(missing_manifest_strings) ; do \
			echo "string	$$lang	$$missing_val	parameter-datasets-$$lang/$$missing_val.tsv" >> $@ ; \
		done ; \
	done


$(experiment)/schema.org.tt:
	mkdir -p $(experiment)
	$(genie) schemaorg-process-schema -o $@ $(process_schemaorg_flags) --domain $(experiment) --class-name $($(experiment)_class_name)  --white-list $($(experiment)_white_list)


$(multilingual_scripts)/../schema_data_processed/$(experiment)/%/data.json: $(experiment)/schema.org.tt $(multilingual_scripts)/../schema_data/$(experiment)/%/*.json
	mkdir -p $(multilingual_scripts)/../schema_data_processed/$(experiment)/$*
	$(genie) schemaorg-normalize-data --data-output $@ --thingpedia $(experiment)/schema.org.tt $(multilingual_scripts)/../schema_data/$(experiment)/$*/*.json --class-name $($(experiment)_class_name)


$(experiment)/schema.trimmed.tt : $(experiment)/schema.org.tt $(multilingual_scripts)/../schema_data_processed/$(experiment)/en/data.json
	$(genie) schemaorg-trim-class --thingpedia $(experiment)/schema.org.tt -o $@ --data $(multilingual_scripts)/../schema_data_processed/$(experiment)/en/data.json --entities $(experiment)/entities.json --domain $(experiment)


$(experiment)/constants.tsv: $(experiment)/parameter-datasets.tsv $(experiment)/schema.trimmed.tt
	$(genie) sample-constants -o $@ --parameter-datasets $(experiment)/parameter-datasets.tsv --thingpedia $(experiment)/schema.trimmed.tt --devices $($(experiment)_class_name)
	cat $(geniedir)/data/en-US/constants.tsv >> $@


$(experiment)/schema.tt: $(experiment)/constants.tsv $(experiment)/schema.trimmed.tt $(experiment)/parameter-datasets.tsv
	$(genie) auto-annotate -o $@ --constants $(experiment)/constants.tsv --thingpedia $(experiment)/schema.trimmed.tt --functions $($(experiment)_white_list) $(update_canonical_flags) --parameter-datasets $(experiment)/parameter-datasets.tsv --dataset schemaorg --debug


schema_crawl_%:
	python3 $(multilingual_scripts)/schema_crawler.py --language $* --init_urls $($(experiment)_$*_init_url) --base_urls $($(experiment)_$*_base_url) --url_patterns $($(experiment)_$*_url_pattern) --experiment $(experiment) --schema_type $($(experiment)_schema_type) --target_size $(crawl_target_size) --output_file $(multilingual_scripts)/../schema_data/$(experiment)/$*/raw_data.json


schema_crawl_all_langs:
	for lang in $(oht_languages_plus_en) ; do \
		make schema_crawl_$$lang ; \
	done


all_experiments_params_schemas:
	for experiment in $(all_experiments); do \
		make -B experiment=$$experiment $$experiment/parameter-datasets.tsv ; \
		make -B experiment=$$experiment $$experiment/schema.tt ; \
	done
