#!/usr/bin/env python3

import os, collections
import cx_Oracle

out_file = 'test/phony-ontie.kn'

proteins = """
SELECT source_id, name, aliases, synonyms, organism_id, organism_name
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

# A dictionary from tax_id to a list of synonyms.
alternative_terms = collections.defaultdict(list)

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

	with open(out_file, 'w') as ontie:
		cur.execute(organisms)
		for row in cur:
			add_organism(ontie, row, second_cur)

def add_organism(ontie, row, cur):
	"""For each IEDB taxon, write a stanza to a phony ONTIE.kn file."""
	global alternative_term

	(iri, tax_id, label, rank, parent_tax_id, parent_tax_id_string, parent) = row

	if iri is not None:
		curie = iri.replace(base, prefix)
	else:
		curie = ""
	label = clean_name(label)
	parent = clean_name(parent)
	if rank:
		rank = clean_name(rank)

	ontie.write(': %s\n' % curie)
	ontie.write('apply template: taxon class\n')
	ontie.write(' label: %s\n' % label)
	ontie.write(' parent taxon: %s\n' % parent)
	if ',' in parent_tax_id_string:
		superclasses = get_superclasses(parent_tax_id_string, parent, cur)
		for sc in superclasses:
			ontie.write('subclass of: %s\n' % sc)
	for alternative_term in alternative_terms[tax_id]:
		ontie.write('alternative term: %s\n' % alternative_term)
	if rank:
		ontie.write('rank: %s\n' % rank)
	ontie.write('\n')

	return True

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
