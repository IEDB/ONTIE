ROBOT := java -jar build/robot.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_"

DATE := $(shell date +%Y-%m-%d)

build build/validate build/diff build/master build/validation:
	mkdir -p $@

build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.9.10/robot.jar

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
MODULES := $(foreach I,$(IMPORTS),build/$(I)-import.ttl)

$(OWL_IMPORTS): | build
	curl -Lk -o $@ http://purl.obolibrary.org/obo/$(notdir $@)

build/terms.txt: src/ontology/templates/external.tsv | build
	awk -F '\t' '{print $$1}' $< | tail -n +3 | sed '/NCBITaxon:/d' > $@

ANN_PROPS := IAO:0000112 IAO:0000115 IAO:0000118 IAO:0000119

build/%-import.ttl: build/%.owl build/terms.txt | build/robot.jar
	$(eval ANNS := $(foreach A,$(ANN_PROPS),--term "$(A)"))
	$(ROBOT) extract --method MIREOT \
	--input $< \
	--upper-terms $(word 2,$^) \
	--lower-terms $(word 2,$^) \
	remove \
	--select complement \
	--drop-axiom-annotations all \
	remove \
	$(ANNS) \
	--select complement \
	--select annotation-properties \
	--output $@

build/imports.ttl: $(MODULES) | build/robot.jar
	$(eval INS := $(foreach M,$(MODULES), --input $(M)))
	$(ROBOT) merge $(INS) --output $@

.PHONY: clean-imports
clean-imports:
	rm -rf $(OWL_IMPORTS)

refresh-imports: clean-imports build/imports.ttl


# Main tasks

.PHONY: update
update:
	make all build/diff.html build/report.html

.PHONY: clean
clean:
	rm -rf build/

.PHONY: test
test: build/report.tsv

.PHONY: all
all: test


INDEX := src/ontology/templates/index.tsv
build/report-problems.tsv: src/scripts/report.py $(TABLES) | build
	rm -f $@ && touch $@
	python3 $< \
	--index $(INDEX) \
	--templates $(filter-out $(INDEX), $(TABLES)) > $@
	[ -s $@ ] || echo "table    cell" > $@

build/ontie.owl:
	cp ontie.owl $@

build/template-problems.tsv: $(TABLES) | build/robot.jar
	$(ROBOT) template \
	$(foreach T,$(TABLES),--template $(T)) \
	--force true \
	--errors $@
	[ -s $@ ] || echo "table	cell" > $@

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

site/:
	mkdir -p $@

site/index.html: src/scripts/static.py | site/
	python3 $<

site/documentation.html.html: src/scripts/static.py doc/api.md | site/
	python3 $<

site/file/:
	mkdir -p $@

site/file/ontie.owl: ontie.owl | site/file/
	cp $< $@

site/file/disease-tree.owl: disease-tree.owl | site/file/
	cp $< $@

site/file/%.tsv: build/%.tsv | site/file/
	cp $< $@

.PHONY: build-static
build-static: site/index.html
build-static: site/documentation.html
build-static: site/file/ontie.owl
build-static: site/file/ontie.tsv
build-static: site/file/disease-tree.owl
build-static: site/file/disease-tree.tsv

.PHONY: build-all
build-all: build/ontology.built build/ontie.built build/disease-tree.built

.PHONY: foo
foo: build-all build-static
