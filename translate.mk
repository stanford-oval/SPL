-include paraphrase_gt_quoted.mk
-include paraphrase_marian_unquoted.mk
-include back_translate_gt_quoted.mk
-include back_translate_marian_quoted.mk
-include back_translate_marian_unquoted.mk
-include translate_gt_quoted.mk
-include translate_gt_unquoted.mk
-include translate_marian_unquoted.mk
-include translate_marian_direct.mk
-include translate_gt_direct.mk
-include back_translate_marian_direct.mk
-include back_translate_gt_direct.mk


batch_translate_no_glossary_all_langs:
	for lang in $(subset_languages) ; do \
		make batch_translate_no_glossary_$$lang ; \
	done


batch_translate_quoted_all_langs:
	for lang in $(subset_languages) ; do \
		make batch_translate_quoted_$$lang ; \
	done


$(experiment)/upload_glossary: $(experiment)/en/aug-en/unquoted-qpis
	python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 --update_glossary --glossary_bucket $(glossary_bucket)  --input_local_path ./$(experiment)/en/aug-en/unquoted-qpis --input_names $(foreach name, $(all_names), $(name).tsv) --glossary_type ${glossary_type} --glossary_local_path $(multilingual_scripts)/extras/ --source_lang en --target_langs $(all_languages)


$(experiment)/upload_data: $(experiment)/en/aug-en/unquoted-qpis-gt
	python3 $(multilingual_scripts)/translate_v3.py --project_id $(gt_project_id) --project_number $(gt_project_number) --credential_file $(gt_credential_file) \
	 --update_dataset --input_local_path ./$(experiment)/en/aug-en/unquoted-qpis-gt --input_names $(foreach name, $(all_names), $(name).tsv) --input_bucket $(input_bucket)

