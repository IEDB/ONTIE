### Workflow
#
# #### Edit existing terms
# 1. [Edit all templates](./src/scripts/cogs.sh) the Google Sheet
# 2. [Validate](validate) sheet
#
# #### Add a new term
# - [assays](./src/scripts/generate-form.sh?template=assays)
# - [complex](./src/scripts/generate-form.sh?template=complex)
# - [disease](./src/scripts/generate-form.sh?template=disease)
# - [other](./src/scripts/generate-form.sh?template=other)
# - [protein](./src/scripts/generate-form.sh?template=protein)
# - [taxon](./src/scripts/generate-form.sh?template=taxon)
#
# #### Review changes
# 3. [View table diffs](build/diff/diff.html)
# 4. [Update](update) ontology files
# 5. View the results:
#     - [View ROBOT report](build/report.html)
#     - [Browse Trees](./src/scripts/tree.sh)
#     - [Download ontie.owl](ontie.owl)
#
# #### Commit Changes
#
# 1. Run [Status](git status) to see changes
# 2. Run [Commit](git commit) and enter message
# 3. Run [Push](git push) and create a new Pull Request
#
# ### Before you go...
# [Clean Build Directory](clean) [Destroy Google Sheet](destroy)

ROBOT := java -jar build/robot.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_"
COGS := cogs

DATE := $(shell date +%Y-%m-%d)

build build/validate build/diff build/master build/validation:
	mkdir -p $@

build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.9.0/robot.jar

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

SHEETS := predicates index external protein complex disease taxon assays other obsolete
TABLES := $(foreach S,$(SHEETS),src/ontology/templates/$(S).tsv)

# ONTIE from templates

ontie.owl: $(TABLES) src/ontology/metadata.ttl build/imports.ttl | build/robot.jar
	$(ROBOT) template \
	$(foreach T,$(TABLES),--template $(T)) \
	merge \
	--input src/ontology/metadata.ttl \
	--input build/imports.ttl \
	--include-annotations true \
	annotate \
	--ontology-iri "https://ontology.iedb.org/ontology/$@" \
	--version-iri "https://ontology.iedb.org/ontology/$(DATE)/$@" \
	--output $@

build/ontie-base.owl: ontie.owl | build/robot.jar
	$(ROBOT) remove \
	--input $< \
	--base-iri ONTIE \
	--axioms external \
	--output $@

build/report.html: build/ontie-base.owl | build/robot.jar
	$(ROBOT) report \
	--input $< \
	--standalone true \
	--fail-on none \
	--output $@

build/report.tsv: build/ontie-base.owl | build/robot.jar
	$(ROBOT) report --input $< --print 10 --output $@

build/diff.html: ontie.owl | build/robot.jar
	git show master:ontie.owl > build/ontie.master.owl
	$(ROBOT) diff -l build/ontie.master.owl -r $< -f html -o $@

DIFF_TABLES := $(foreach S,$(SHEETS),build/diff/$(S).html)

# Workaround to make sure master branch exists
build/fetched.txt:
	git fetch origin master:master && date > $@

build/diff/%.html: src/ontology/templates/%.tsv build/fetched.txt | build/master build/diff
	git show master:$< > build/master/$(notdir $<)
	daff build/master/$(notdir $<) $< --output $@ --fragment

build/diff/diff.html: src/scripts/diff.py src/scripts/diff.html.jinja2 $(DIFF_TABLES)
	python3 $< src/scripts/diff.html.jinja2 $(SHEETS) > $@

diffs: $(DIFF_TABLES)


# Imports

IMPORTS := doid obi
OWL_IMPORTS := $(foreach I,$(IMPORTS),build/$(I).owl)
DBS := build/ontie.db $(foreach I,$(IMPORTS),build/$(I).db)
MODULES := $(foreach I,$(IMPORTS),build/$(I)-import.ttl)

dbs: $(DBS)

$(OWL_IMPORTS): | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/$(notdir $@)

build/%.db: src/scripts/prefixes.sql build/%.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)
	sqlite3 $@ "CREATE INDEX idx_stanza ON statements (stanza);"
	sqlite3 $@ "CREATE INDEX idx_subject ON statements (subject);"
	sqlite3 $@ "CREATE INDEX idx_predicate ON statements (predicate);"
	sqlite3 $@ "CREATE INDEX idx_object ON statements (object);"
	sqlite3 $@ "CREATE INDEX idx_value ON statements (value);"
	sqlite3 $@ "ANALYZE;"

build/terms.txt: src/ontology/templates/external.tsv | build
	awk -F '\t' '{print $$1}' $< | tail -n +3 | sed '/NCBITaxon:/d' > $@

ANN_PROPS := IAO:0000112 IAO:0000115 IAO:0000118 IAO:0000119

build/%-import.ttl: build/%.db build/terms.txt
	$(eval ANNS := $(foreach A,$(ANN_PROPS), -p $(A)))
	python3 -m gizmos.extract -d $< -T $(word 2,$^) $(ANNS) -n > $@

build/imports.ttl: $(MODULES) | build/robot.jar
	$(eval INS := $(foreach M,$(MODULES), --input $(M)))
	$(ROBOT) merge $(INS) --output $@

.PHONY: clean-imports
clean-imports:
	rm -rf $(OWL_IMPORTS)

refresh-imports: clean-imports build/imports.ttl


# Tree Building

build/ontie.db: src/scripts/prefixes.sql ontie.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < ontie.owl
	sqlite3 $@ "CREATE INDEX idx_stanza ON statements (stanza);"
	sqlite3 $@ "CREATE INDEX idx_subject ON statements (subject);"
	sqlite3 $@ "CREATE INDEX idx_predicate ON statements (predicate);"
	sqlite3 $@ "CREATE INDEX idx_object ON statements (object);"
	sqlite3 $@ "CREATE INDEX idx_value ON statements (value);"
	sqlite3 $@ "ANALYZE;"


# Main tasks

.PHONY: update
update:
	make all dbs build/diff.html build/report.html

.PHONY: clean
clean:
	rm -rf build/

.PHONY: test
test: build/report.tsv

.PHONY: all
all: test


# COGS Tasks

# Create a new Google sheet with branch name & share it with provided email

COGS_SHEETS := $(foreach S,$(SHEETS),.cogs/tracked/$(S).tsv)

.PHONY: load
load: $(COGS_SHEETS)
	mv .cogs/sheet.tsv sheet.tsv
	sed s/0/2/ sheet.tsv > .cogs/sheet.tsv
	rm sheet.tsv

.cogs/tracked/%.tsv: src/ontology/templates/%.tsv | .cogs
	$(COGS) add $<

.PHONY: push
push:
	$(COGS) push

.PHONY: show
show:
	$(COGS) open

.PHONY: destroy
destroy:
	$(COGS) delete -f

# Tasks after editing Google Sheets

.PHONY: validate
validate: update-sheets apply push

.PHONY: update-sheets
update-sheets:
	$(COGS) fetch && $(COGS) pull

INDEX := src/ontology/templates/index.tsv
build/report-problems.tsv: src/scripts/report.py $(TABLES) | build
	rm -f $@ && touch $@
	python3 $< \
	--index $(INDEX) \
	--templates $(filter-out $(INDEX), $(TABLES)) > $@
	[ -s $@ ] || echo "table    cell" > $@

VALVE_CONFIG := $(foreach f,$(shell ls src/ontology/validation),src/ontology/validation/$(f))

build/valve-problems.tsv: $(VALVE_CONFIG) $(TABLES)
	valve src/ontology/validation src/ontology/templates -r 3 -o $@

build/ontie.owl:
	cp ontie.owl $@

build/template-problems.tsv: $(TABLES) | build/robot.jar
	$(ROBOT) template \
	$(foreach T,$(TABLES),--template $(T)) \
	--force true \
	--errors $@
	[ -s $@ ] || echo "table	cell" > $@

.PHONY: apply
apply: build/report-problems.tsv build/template-problems.tsv build/valve-problems.tsv
	$(COGS) clear all
	$(COGS) apply $^

.PHONY: sort
sort: src/ontology/templates/
	src/scripts/sort-templates.py


bin/:
	mkdir $@

# Install LDTab if not already present
ifeq ($(shell command -v ldtab),)
bin/ldtab.jar: | bin/
	curl -L -o $@ 'https://github.com/ontodev/ldtab.clj/releases/download/v2023-12-21/ldtab.jar'
bin/ldtab: bin/ldtab.jar
	echo '#!/bin/sh' > $@
	echo 'java -jar "$$(dirname $$0)/ldtab.jar" "$$@"' >> $@
	chmod +x $@
deps: bin/ldtab
endif

export PATH := $(shell pwd)/bin:$(PATH)

build/ontology.owl: ontie.owl
	cp $< $@

build/%.owl: %.owl
	cp $< $@

build/%.tsv: build/%.owl src/schema/prefix.tsv | build/
	$(eval DB := build/$(subst -,_,$*).db)
	rm -f $@ $(DB)
	ldtab init $(DB)
	ldtab prefix $(DB) $(word 2,$^)
	ldtab import $(DB) $<
	ldtab export $(DB) $@
	rm $(DB)

.nanobot.db: src/schema/* build/ontology.tsv build/ontie.tsv build/disease-tree.tsv
	rm -f $@
	nanobot init

build/%.built: .nanobot.db
	$(eval TABLE := $(subst -,_,$*))
	sqlite3 $< "CREATE INDEX IF NOT EXISTS idx_$(TABLE)_subject ON $(TABLE)(subject)"
	sqlite3 $< "CREATE INDEX IF NOT EXISTS idx_$(TABLE)_predicate ON $(TABLE)(predicate)"
	sqlite3 $< "CREATE INDEX IF NOT EXISTS idx_$(TABLE)_object ON $(TABLE)(object)"
	sqlite3 $< "ANALYZE $(TABLE)"

build/download/:
	mkdir -p $@

build/download/ontie.owl: ontie.owl | build/download/
	cp $< $@

build/download/disease-tree.owl: disease-tree.owl | build/download/
	cp $< $@

build/download/%.tsv: build/%.tsv | build/download/
	cp $< $@

.PHONY: downloads
downloads: build/download/ontie.owl
downloads: build/download/ontie.tsv
downloads: build/download/disease-tree.owl
downloads: build/download/disease-tree.tsv

.PHONY: build-all
build-all: build/ontology.built build/ontie.built build/disease-tree.built

.PHONY: foo
foo: build-all downloads
