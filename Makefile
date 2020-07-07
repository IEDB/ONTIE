### Workflow
#
# 1. Edit the [ONTIE Google Sheet](https://docs.google.com/spreadsheets/d/1DFij_uxMH74KR8bM-wjJYa9qITJ81MvFIKUSpZRPelw/edit)
# 2. Run [Update](update)
# 3. View the results:
#     - [ROBOT report](build/report.tsv)
#     - [Tree](build/ontie-tree.html)

KNODE := java -jar knode.jar
XLSX := xlsx2csv --delimiter tab --escape --ignoreempty
ROBOT := java -jar build/robot.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_"

DATE := $(shell date +%Y-%m-%d)

build:
	mkdir $@

build/robot.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

# ROBOT templates from Google sheet

build/ontie.xlsx: | build
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1DFij_uxMH74KR8bM-wjJYa9qITJ81MvFIKUSpZRPelw/export?format=xlsx"

SHEETS := predicates index external protein disease taxon other
TABLES := $(foreach S,$(SHEETS),src/ontology/templates/$(S).tsv)

tables: $(TABLES)

$(TABLES): build/ontie.xlsx
	$(XLSX) -n $(notdir $(basename $@)) $< > $@

# ONTIE from templates

ontie.owl: $(TABLES) src/ontology/metadata.ttl | build/robot.jar
	$(ROBOT) template \
	$(foreach T,$(TABLES),--template $(T)) \
	merge \
	--input $(lastword $^) \
	--include-annotations true \
	annotate \
	--ontology-iri "https://ontology.iebd.org/ontology/$@" \
	--version-iri "https://ontology.iebd.org/ontology/$(DATE)/$@" \
	--output $@

build/report.tsv: ontie.owl
	$(ROBOT) report --input $< --output $@ --print 20


# Tree Building

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/ontie-tree.html: ontie.owl | build/robot-tree.jar
	java -jar build/robot-tree.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_" \
	tree --input $< --tree $@


# Main tasks

.PHONY: update
update:
	rm -rf build/ontie.xlsx $(TABLES)
	make build/ontie-tree.html test

.PHONY: clean
clean:
	rm -rf build/

.PHONY: test
test: build/report.tsv

.PHONY: all
all: test
