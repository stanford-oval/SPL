
server_port ?= 8400
server_locale ?= fa

$(experiment)/%/run_server: $(experiment)/models/%/best.pth
	$(genie) server \
	  --locale $(server_locale) --port $(server_port) \
	  --nlu-model $(experiment)/models/$* \
	  --thingpedia $(if $(findstring /,$(experiment)),$(dir $(experiment)),$(experiment))/schema.tt

run_almond_server:
	export THINGENGINE_HOME=$(realpath ./home) ; export THINGENGINE_NLP_URL=http://127.0.0.1:8400 ; node $(almond_server)/main.js --locale $(server_locale)

run_almond_server:
	export THINGENGINE_HOME=$(realpath ./home) ; export THINGENGINE_NLP_URL=http://127.0.0.1:8400 ; node $(almond_server)/main.js --locale $(server_locale)


$(experiment)/%/annotate:  $(experiment)/models/%/best.pth
	$(genie) manual-annotate \
	  --server "file://$(abspath $(dir $<))" \
	  --thingpedia $(experiment)/schema.tt \
	  --annotated $(experiment)/$(eval_set)/annotated.tsv \
	  --dropped $(experiment)/$(eval_set)/dropped.tsv \
	  --offset $(annotate_offset) \
	  $(experiment)/$(eval_set)/input.txt


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
