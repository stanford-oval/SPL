SHELL := /bin/bash

-include ./project.config
-include ./arguments.config
-include ./private.config

-include data.mk
-include translate.mk
-include general.mk
-include schema.mk
-include process_oht.mk
-include emnlp.mk
-include emnlp_train.mk
-include emnlp_eval.mk
-include emnlp_translation.mk
-include calculate_scores.mk
-include create_sts.mk


.PHONY: all syncup syncdown clean %_eval eval-all-% %_train train-all upload_data \
 upload_glossary batch_translate_% translate_%



