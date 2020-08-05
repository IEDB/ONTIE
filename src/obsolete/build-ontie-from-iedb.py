#!/usr/bin/env python3

import os, collections
import cx_Oracle

out_file = 'test/phony-ontie.kn'

proteins = """
SELECT iri, 
	source_id, 
	name, 
	aliases, 
	synonyms, 
	organism_id, 
	organism_name
FROM source
WHERE database = 'IEDB'
  AND organism_id IS NOT NULL
  AND organism_name IS NOT NULL
ORDER BY source_id
"""

organisms = """
SELECT o1.iri,
  o1.organism_id,
  o1.organism_name AS label,
  o1.rank,
  o1.parent_tax_id,
  o1.parent_tax_id_string,
  o2.organism_name AS parent
FROM organism o1, organism o2
WHERE o1.parent_tax_id = o2.organism_id
  AND o1.organism_id >= 10000000
ORDER BY o1.organism_id
"""

synonyms = """
SELECT tax_id, name_txt
FROM names
WHERE name_class = 'synonym'
	AND tax_id >= 10000000
ORDER BY tax_id
"""

parent_name = """
SELECT organism_id, organism_name
FROM organism
WHERE organism_id = {0}
"""

base = "https://ontology.iedb.org/ontology/ONTIE_"
prefix = "ONTIE:"
fake_prefix = "TEMP:%d"

# A dictionary from tax_id to a list of synonyms.
alternative_terms = collections.defaultdict(list)

ontie_map = {}
fake_id = 9000000

def main():
	"""Connect to the database to query for IEDB taxon, then create a 'phony'
	ONTIE.kn file to compare to the original ONTIE.kn file."""
	# Connect to the Oracle DB
	connect_string = "newdb/newdb@10.0.3.197:1521/iedbprod"
	conn = cx_Oracle.connect(connect_string, encoding = "UTF-8", nencoding = "UTF-8")
	print("Connecting: {}".format(connect_string))
	cur = conn.cursor()
	second_cur = conn.cursor()

	# Collect alternative terms
	cur.execute(synonyms)
	for row in cur:
		(tax_id, name) = row
		alternative_terms[tax_id].append(name.strip())
	# Collect organisms
	cur.execute(organisms)
	for row in cur:
		add_organism(row, second_cur)
	# Collect proteins
	cur.execute(proteins)
	for row in cur:
		add_protein(row)

	# Build ONTIE in CURIE order
	with open(out_file, 'w') as f:
		for key in sorted(ontie_map.keys()):
			f.write(ontie_map[key])

def add_organism(row, cur):
	"""For each IEDB taxon, write a stanza to a phony ONTIE.kn file."""
	global ontie_map, fake_id

	(iri, tax_id, label, rank, parent_tax_id, parent_tax_id_string, parent) = row

	if iri is not None:
		curie = iri.replace(base, prefix)
	else:
		curie = fake_prefix % fake_id
		fake_id += 1
	label = clean_name(label)
	parent = clean_name(parent)
	if rank:
		rank = clean_name(rank)

	stanza = ''
	stanza += (': %s\n' % curie)
	stanza += ('apply template: taxon class\n')
	stanza += (' label: %s\n' % label)
	stanza += (' parent taxon: %s\n' % parent)
	if ',' in parent_tax_id_string:
		superclasses = get_superclasses(parent_tax_id_string, parent, cur)
		for sc in superclasses:
			stanza += ('subclass of: %s\n' % sc)
	for alternative_term in alternative_terms[tax_id]:
		stanza += ('alternative term: %s\n' % alternative_term)
	if rank:
		stanza += ('rank: %s\n' % rank)
	stanza += ('\n')

	ontie_map[curie] = stanza

def add_protein(row):
	"""For each IEDB SRC protein, write a stanza to a phony ONTIE.kn file."""
	global ontie_map, fake_id

	(iri, source_id, name, aliases, synonyms, organism_id, organism) = row

	if iri is not None:
		curie = iri.replace(base, prefix)
	else: 
		curie = fake_prefix % fake_id
		fake_id += 1
	name = clean_name(name)
	organism = clean_name(organism)

	label = '%s (%s)' % (name, organism)
	if not aliases:
		aliases = ''
	if synonyms:
		synonyms = synonyms.read()
	else:
		synonyms = ''
	alternative_terms = aliases.split(', ') + synonyms.split(', ')

	stanza = ''
	stanza += (': %s\n' % curie)
	stanza += ('apply template: protein class\n')
	stanza += (' label: %s\n' % name)
	stanza += (' taxon: %s\n' % organism)
	for alternative_term in alternative_terms:
		alternative_term = alternative_term.strip()
		if alternative_term != '':
			stanza += ('alternative term: %s\n' % alternative_term)
	stanza += ('\n')

	ontie_map[curie] = stanza

def clean_name(name):
	"""Return a tab-replaced name."""
	return name.strip().replace('\t', ' ')

def get_superclasses(parent_tax_id_string, parent, cur):
	"""Given a string with multiple parent IDs, the original parent name, 
	and a cursor to query with, get the labels and return them as a list,
	excluding the original parent name."""
	superclasses = []
	for s in parent_tax_id_string.split(','):
		query = parent_name.format(s)
		cur.execute(query)
		for row in cur:
			(organism_id, organism_name) = row
			organism_name = clean_name(organism_name)
			if organism_name != parent:
				superclasses.append(organism_name)
	return superclasses

# Execute
if __name__ == '__main__':
	main()
