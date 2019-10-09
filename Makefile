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

build/doid.owl: | build
	$(ROBOT) merge \
	--input-iri http://purl.obolibrary.org/obo/doid.owl \
	reason \
	relax \
	reduce \
	remove \
	--select "equivalents" \
	--output $@

build/doid-external.owl: build/doid.owl src/doid-terms.txt
	$(ROBOT) filter \
	--input $< \
	--term-file $(word 2,$^) \
	--select "self parents equivalents" \
	--trim false \
	--output $@

build/ext-doid-terms.txt: build/doid-external.owl
	$(ROBOT) query \
	--input $< \
	--query src/get-external-doid-terms.rq $(basename $@).tsv
	tail -n +2 $(basename $@).tsv | awk -F'"' '{print $$2}' > $@
	rm $(basename $@).tsv

build/doid-external-plus.owl: build/doid.owl build/ext-doid-terms.txt
	$(ROBOT) extract \
	--input $< \
	--method MIREOT \
	--lower-terms $(word 2,$^) \
	--output $@

build/doid-subset.owl: build/doid.owl build/doid-external-plus.owl build/doid-external.owl
	$(ROBOT) extract \
	--input $< \
	--method MIREOT \
	--lower-terms src/doid-terms.txt \
	merge \
	--input $(word 2,$^) \
	--input $(word 3,$^) \
	remove \
	--term-file src/doid-remove.txt \
	query \
	--update src/rearrange-do.ru \
	--output $@

build/doid-ext-remove.txt: build/doid-subset.owl build/ext-doid-terms.txt
	$(ROBOT) query \
	--input $< \
	--query src/get-external-doid-terms.rq $(basename $@).tsv
	tail -n +2 $(basename $@).tsv | awk -F'"' '{print $$2}' > $@.tmp
	comm -23 $@.tmp $(word 2,$^) > $@
	rm $(basename $@).tsv $@.tmp

build/remove-doid-classes.txt: build/doid-subset.owl
	$(ROBOT) query \
	--input $< \
	--query src/remove-doid-classes.rq $(basename $@).tsv
	tail -n +2 $(basename $@).tsv | awk -F'"' '{print $$2}' > $@
	rm $(basename $@).tsv

build/doid-module.owl: build/doid-subset.owl build/remove-doid-classes.txt build/doid-ext-remove.txt
	$(ROBOT) remove \
	--input $< \
	--term-file $(word 2,$^) \
	remove \
	--term-file $(word 3,$^) \
	remove \
	--term-file src/doid-remove.txt \
	reduce \
	--output $@

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
load: knode.edn build/ncbitaxon.owl build/ncbitaxon-merged.ttl build/ncbitaxon-obsolete.ttl build/doid-module.owl
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
