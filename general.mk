
server_port ?= 8400
server_locale ?= en-US


$(experiment)/%/run_server: $(experiment)/models/%/best.pth
	$(genie) server \
	  --locale $(server_locale) --port $(server_port) \
	  --nlu-model $(experiment)/models/$* \
	  --thingpedia $(if $(findstring /,$(experiment)),$(dir $(experiment)),$(experiment))/schema.tt

run_almond_server:
	export THINGENGINE_HOME=$(realpath ./home) ; export THINGENGINE_NLP_URL=http://127.0.0.1:8400 ; export LOCALE=$(server_locale) ; node $(almond_server)/main.js


$(experiment)/%/annotate:  $(experiment)/models/%/best.pth
	$(genie) manual-annotate \
	  --server "file://$(abspath $(dir $<))" \
	  --thingpedia $(experiment)/schema.tt \
	  --annotated $(experiment)/$(eval_set)/annotated.tsv \
	  --dropped $(experiment)/$(eval_set)/dropped.tsv \
	  --offset $(annotate_offset) \
	  $(experiment)/$(eval_set)/input.txt

##############
### evaluation
##############

.PRECIOUS: $(experiment)/models/%/best.pth

s3_model_dir=
s3_metrics_output=
metrics_output=
artifact_lang=
is_dlg=

$(experiment)/models/%/best.pth:
	mkdir -p $(experiment)/models/
	if [ "${s3_model_dir}" != "" ] ; then \
		aws s3 sync --exclude '*/dataset/*' --exclude '*/cache/*' --exclude 'iteration_*.pth' --exclude '*_optim.pth' ${s3_model_dir} $(experiment)/models/$*/ ; \
	else \
		aws s3 sync --exclude '*/dataset/*' --exclude '*/cache/*' --exclude 'iteration_*.pth' --exclude '*_optim.pth' s3://geniehai/$(owner)/models/${project}/$(if $(findstring /,$(experiment)),$(patsubst %/,%,$(dir $(experiment))),$(experiment))/$*/ $(experiment)/models/$*/ ; \
	fi

# .results_single instead of .results to avoid clash with dialog target command
$(experiment)/$(eval_set)/%.results_single: $(experiment)/models/%/best.pth
	mkdir -p $(experiment)/$(eval_set)
	$(genie) evaluate-server $(input_eval_server) --output-errors $(experiment)/$(eval_set)/"$*".errors --url "file://$(abspath $(dir $<))" --thingpedia $(experiment)/schema.tt $(eval_oracle) --debug --csv-prefix $(eval_set) --csv $(evalflags) --max-complexity 3 -o $(experiment)/$(eval_set)/$*.results.tmp | tee $(experiment)/$(eval_set)/$*.debug
	mv $(experiment)/$(eval_set)/$*.results.tmp $(experiment)/$(eval_set)/$*.results


evaluate-output-artifacts-%:
	mkdir -p `dirname $(s3_metrics_output)`
	mkdir -p $(metrics_output)
	echo s3://geniehai/${owner}/workdir/${project}/${experiment}/${eval_set}/${artifact_lang}/ > $(s3_metrics_output)
	cp -r $(experiment)/${eval_set}/* $(metrics_output)
	python3 $(multilingual_scripts)/write_kubeflow_metrics.py `if ${is_dlg} ; then echo "--is_dlg" ; fi` --dialogue_results $(experiment)/${eval_set}/$*.dialogue.results --nlu_results $(experiment)/${eval_set}/$*.nlu.results


dryrun ?= --dryrun

syncup:
	aws s3 sync --size-only ./ s3://geniehai/$(owner)/workdir/$(project) --exclude '.git*' --exclude '.idea*' --exclude '*.DS_Store*' --exclude '*.embeddings*' --exclude '*/eval/*' --exclude '*/test/*' --exclude '*/models/*' --exclude '*process_eval_logs.csv*' --exclude '*pyter*' --exclude '*process_eval_logs*'  $(dryrun)

syncdelete:
	aws s3 rm --size-only --recursive s3://geniehai/$(owner)/workdir/${project}/ $(dryrun)

syncdown:
	aws s3 sync --size-only s3://geniehai/$(owner)/workdir/$(project) ./ --exclude '*' --include '*unquoted-qpis-translated*' --include '*/marian/*' --include '*/gt/*' --include "*/eval/*" --include "*/test/*" --include '*final-direct*' $(dryrun)

deepclean:
	for experiment in $(all_experiments) ; do \
		rm -rf ./$$experiment/* ; \
	done
