KNODE := java -jar knode.jar
ROBOT := java -jar build/robot.jar

# Fetch ontology files
build:
	mkdir $@

build/ncbitaxon.owl: | build
	curl -L -o $@ "http://purl.obolibrary.org/obo/ncbitaxon.owl"

build/chebi.owl: | build
	curl -L -o $@ "http://purl.obolibrary.org/obo/chebi.owl"

build/obi.owl: | build
	curl -L -o $@ "http://purl.obolibrary.org/obo/obi.owl"

build/mro.owl: | build
	curl -L -o $@ "https://github.com/IEDB/MRO/raw/master/iedb/mro-iedb.owl"


# Extra NCBI tasks
build/taxdmp.zip: | build
	curl -L "ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdmp.zip" > $@

build/merged.dmp: build/taxdmp.zip
	unzip -qc $< merged.dmp > $@

build/delnodes.dmp: build/taxdmp.zip
	unzip -qc $< delnodes.dmp > $@

build/ncbitaxon-merged.ttl: src/ncbitaxon-merged.py build/merged.dmp
	$^ $@

build/ncbitaxon-obsolete.ttl: src/ncbitaxon-obsolete.py build/delnodes.dmp
	$^ $@


# Load data into KnoDE

.PHONY: load
load: knode.edn build/ncbitaxon.owl build/ncbitaxon-merged.ttl build/ncbitaxon-obsolete.ttl
	$(KNODE) load-config $<

# Old load methods

.PHONY: load-ontie
load-ontie: ontology/context.kn ontology/external.tsv ontology/predicates.tsv ontology/index.tsv ontology/templates.kn ontology/ontie.kn
	$(KNODE) load ONTIE $^

.PHONY: load-ncbitaxonomy
load-ncbitaxonomy: build/ncbitaxon.owl build/ncbitaxon-merged.ttl build/ncbitaxon-obsolete.ttl
	$(KNODE) load NCBITaxonomy build/ncbitaxon.owl
	$(KNODE) load NCBITaxonomy build/ncbitaxon-merged.ttl
	$(KNODE) load NCBITaxonomy build/ncbitaxon-obsolete.ttl

.PHONY: load-chebi
load-chebi: build/chebi.owl
	$(KNODE) load ChEBI $<

.PHONY: load-obi
load-obi: build/obi.owl
	$(KNODE) load OBI $<

.PHONY: load-mro
load-mro: build/mro.owl
	$(KNODE) load MRO $<


# General tasks
.PHONY: all
all: load

.PHONY: clean
clean:
	rm -rf build/
