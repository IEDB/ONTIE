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

build resources:
	mkdir $@

build/robot.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/master/lastSuccessfulBuild/artifact/bin/robot.jar

UNAME := $(shell uname)
ifeq ($(UNAME), Darwin)
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-apple-darwin
else
	RDFTAB_URL := https://github.com/ontodev/rdftab.rs/releases/download/v0.1.1/rdftab-x86_64-unknown-linux-musl
endif

build/rdftab: | build
	curl -L -o $@ $(RDFTAB_URL)
	chmod +x $@

# ROBOT templates from Google sheet

build/ontie.xlsx: | build
	curl -L -o $@ "https://docs.google.com/spreadsheets/d/1DFij_uxMH74KR8bM-wjJYa9qITJ81MvFIKUSpZRPelw/export?format=xlsx"

SHEETS := predicates index external protein disease taxon other
TABLES := $(foreach S,$(SHEETS),src/ontology/templates/$(S).tsv)

tables: $(TABLES)

$(TABLES): build/ontie.xlsx
	$(XLSX) -n $(notdir $(basename $@)) $< > $@

# ONTIE from templates

ontie.owl: $(TABLES) src/ontology/metadata.ttl build/imports.ttl | build/robot.jar
	$(ROBOT) template \
	$(foreach T,$(TABLES),--template $(T)) \
	merge \
	--input src/ontology/metadata.ttl \
	--input build/imports.ttl \
	--include-annotations true \
	annotate \
	--ontology-iri "https://ontology.iebd.org/ontology/$@" \
	--version-iri "https://ontology.iebd.org/ontology/$(DATE)/$@" \
	--output $@

build/report.tsv: ontie.owl
	$(ROBOT) remove \
	--input $< \
	--base-iri ONTIE \
	--axioms external \
	report \
	--output $@ \
	--print 20

INDEX := src/ontology/templates/index.tsv
build/problems.tsv: src/scripts/report.py $(TABLES)
	python3 $< \
	--index $(INDEX) \
	--templates $(filter-out $(INDEX), $(TABLES)) > $@


# Imports

IMPORTS := doid obi
OWL_IMPORTS := $(foreach I,$(IMPORTS),resources/$(I).owl)
DBS := $(foreach I,$(IMPORTS),resources/$(I).db)
MODULES := $(foreach I,$(IMPORTS),build/$(I)-import.ttl)

$(OWL_IMPORTS): | resources
	curl -Lk -o $@ http://purl.obolibrary.org/obo/$(notdir $@)

resources/%.db: src/scripts/prefixes.sql resources/%.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)

build/terms.txt: src/ontology/templates/external.tsv
	awk -F '\t' '{print $$1}' $< | tail -n +3 | sed '/NCBITaxon:/d' > $@

ANN_PROPS := IAO:0000112 IAO:0000115 IAO:0000118 IAO:0000119

build/%-import.ttl: src/scripts/mireot.py resources/%.db build/terms.txt
	$(eval ANNS := $(foreach A,$(ANN_PROPS), -a $(A)))
	python3 $< -d $(word 2,$^) -t $(word 3,$^) $(ANNS) -n -o $@

build/imports.ttl: $(MODULES) | build/robot.jar
	$(eval INS := $(foreach M,$(MODULES), --input $(M)))
	$(ROBOT) merge $(INS) --output $@

.PHONY: clean-imports
clean-imports:
	rm -rf $(OWL_IMPORTS)

refresh-imports: clean-imports build/imports.ttl


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
	make build/ontie-tree.html

.PHONY: clean
clean:
	rm -rf build/

.PHONY: test
test: build/problems.tsv build/report.tsv

.PHONY: all
all: test
