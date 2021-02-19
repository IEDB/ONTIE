### Workflow
#
# 1. [Edit](./src/scripts/cogs.sh) the Google Sheet
# 2. [Validate](validate) sheet
# 3. [View table diffs](build/diff/diff.html)
# 4. [Update](update) ontology files
# 5. View the results:
#     - [View ROBOT report](build/report.html)
#     - [Browse Trees](./src/scripts/tree.sh)
#     - [Download ontie.owl](ontie.owl)
#
# ### Commit Changes
#
# 1. Run [Status](git status) to see changes
# 2. Run [Commit](git commit) and enter message
# 3. Run [Push](git push) and create a new Pull Request
#
# ### Before you go...
# [Clean Build Directory](clean) [Destroy Google Sheet](destroy)

KNODE := java -jar knode.jar
ROBOT := java -jar build/robot.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_"
ROBOT_REPORT := java -jar build/robot-report.jar --prefix "ONTIE: https://ontology.iedb.org/ontology/ONTIE_"
COGS := cogs

DATE := $(shell date +%Y-%m-%d)

build build/validate build/diff build/master build/validation:
	mkdir -p $@

build/robot.jar: | build
	curl -L -o $@ https://github.com/ontodev/robot/releases/download/v1.8.1/robot.jar

build/robot-report.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/html-report/lastSuccessfulBuild/artifact/bin/robot.jar

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

SHEETS := predicates index external protein complex disease taxon assays other
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
	--ontology-iri "https://ontology.iebd.org/ontology/$@" \
	--version-iri "https://ontology.iebd.org/ontology/$(DATE)/$@" \
	--output $@

build/report.%: ontie.owl | build/robot-report.jar
	$(ROBOT) remove \
	--input $< \
	--base-iri ONTIE \
	--axioms external \
	report \
	--output $@ \
	--standalone true \
	--print 10

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

build/all.db:  src/scripts/prefixes.sql ontie.owl $(OWL_IMPORTS) | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < ontie.owl \
	$(foreach I,$(OWL_IMPORTS), && ./build/rdftab $@ < $(I))
	sqlite3 $@ "CREATE INDEX idx_stanza ON statements (stanza);"
	sqlite3 $@ "CREATE INDEX idx_subject ON statements (subject);"
	sqlite3 $@ "CREATE INDEX idx_predicate ON statements (predicate);"
	sqlite3 $@ "CREATE INDEX idx_object ON statements (object);"
	sqlite3 $@ "CREATE INDEX idx_value ON statements (value);"
	sqlite3 $@ "ANALYZE;"

build/%.db: src/scripts/prefixes.sql build/%.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < $(word 2,$^)
	sqlite3 $@ "INSERT INTO statements VALUES ('owl:deprecated', 'owl:deprecated', 'rdfs:label', null, 'obsolete', null, null);"
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

build/robot-tree.jar: | build
	curl -L -o $@ https://build.obolibrary.io/job/ontodev/job/robot/job/tree-view/lastSuccessfulBuild/artifact/bin/robot.jar

build/ontie.db: src/scripts/prefixes.sql ontie.owl | build/rdftab
	rm -rf $@
	sqlite3 $@ < $<
	./build/rdftab $@ < ontie.owl


# Main tasks

.PHONY: update
update:
	make all dbs

.PHONY: clean
clean:
	rm -rf build/

.PHONY: test
test: build/report.tsv

.PHONY: all
all: test


# COGS Tasks

# Create a new Google sheet with branch name & share it with provided email

COGS_SHEETS := $(foreach S,$(SHEETS),.cogs/$(S).tsv)

.PHONY: load
load: $(COGS_SHEETS)
	mv .cogs/sheet.tsv sheet.tsv
	sed s/0/2/ sheet.tsv > .cogs/sheet.tsv
	rm sheet.tsv

.cogs/%.tsv: src/ontology/templates/%.tsv | .cogs
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
