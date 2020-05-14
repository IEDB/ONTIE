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

TABLES := ontology/predicates.tsv \
          ontology/index.tsv \
          ontology/external.tsv \
          ontology/manual.tsv \
          ontology/protein.tsv \
          ontology/disease.tsv \
          ontology/taxon.tsv \
          ontology/other.tsv

tables: $(TABLES)

$(TABLES): build/ontie.xlsx
	$(XLSX) -n $(notdir $(basename $@)) $< > $@

# ONTIE from templates

ontie.owl: $(TABLES) | build/robot.jar
	$(eval TEMPS := $(foreach T,$(filter-out $<,$^),template --template $(T) --merge-before ))
	$(ROBOT) template \
	--template $< $(TEMPS) \
	annotate \
	--ontology-iri "https://ontology.iebd.org/ontology/$@" \
	--version-iri "https://ontology.iebd.org/ontology/$(DATE)/$@" \
	--output $@

# Main tasks

.PHONY: refresh
refresh:
	rm -rf build/ontie.xlsx
	rm ontology/*.tsv
	make tables

.PHONY: clean
clean:
	rm -rf build/

all: ontie.owl
