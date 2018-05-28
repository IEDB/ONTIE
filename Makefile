


build:
	mkdir $@

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
