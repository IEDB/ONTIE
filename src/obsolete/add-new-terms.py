#!/usr/bin/env python3

import os, collections
import cx_Oracle
import re

# Paths
index_path = 'ontology/index.tsv'
external_path = 'ontology/external.tsv'
organism_map_path = 'organism_map.tsv'
source_map_path = 'source_map.tsv'

# Dict from internal ID to curie
organism_map = {}
source_map = {}

# Dictionaries from NCBI Taxon labels to CURIEs
external = {}
new_external = {}

# A dictionary from tax_id to a list of synonyms.
alternative_terms = collections.defaultdict(list)

# Global ID
ontie_id = 0

synonyms = """
SELECT tax_id, name_txt
FROM names
WHERE name_class = 'synonym'
	AND tax_id >= 10000000
ORDER BY tax_id
"""

organisms = """
SELECT o1.organism_id,
	o1.organism_name AS label,
	o1.rank,
	o1.parent_tax_id,
	o1.parent_tax_id_string AS parents,
	o2.organism_name AS parent
FROM organism o1, organism o2
WHERE o1.parent_tax_id = o2.organism_id
	AND o1.organism_id >= 10000000
	AND o1.iri IS NULL
ORDER BY o1.organism_id
"""

parent_name = """
SELECT organism_id, organism_name
FROM organism
WHERE organism_id = {0}
"""

proteins = """
SELECT source_id, 
	name, 
	aliases, 
	synonyms, 
	organism_id, 
	organism_name
FROM source
WHERE database = 'IEDB'
  AND organism_id IS NOT NULL
  AND organism_name IS NOT NULL
  AND iri IS NULL
ORDER BY source_id
"""

def main():
	"""Determines the last-used ONTIE ID then creates new classes within 
	ontie.kn based on IEDB organisms that do not have an assigned IRI. The file 
	organism_map.tsv is generated with the new classes & their organism tax_id 
	from IEDB. This file is checked for each null IRI entry to ensure duplicate 
	classes are not created if the DB has not yet been updated."""
	init_data()
	print("Last ID: {}".format(ontie_id))

	# Connect to the Oracle DB
	conn = cx_Oracle.connect(os.environ['ORACLE_CONN'])
	print("Connecting: {}".format(os.environ['ORACLE_CONN']))
	cur = conn.cursor()
	additional_cur = conn.cursor()

	# Collect alternative terms
	cur.execute(synonyms)
	for row in cur:
		(tax_id, name) = row
		alternative_terms[tax_id].append(name.strip())

	# Create new organisms in ontology/ontie.kn
	# New IDs & are also added ontology/index.tsv
	# And the new mappings are added in organism_map.tsv
	orgs_added = 0
	proteins_added = 0
	with open('ontology/ontie.kn', 'a') as ontie:
		with open(index_path, 'a') as index:
			with open(organism_map_path, 'a') as orgs:
				cur.execute(organisms)
				for row in cur:
					if add_organism(ontie, index, orgs, row, additional_cur):
						orgs_added += 1
			with open(source_map_path, 'a') as src:
				cur.execute(proteins)
				for row in cur:
					if add_protein(ontie, index, src, row):
						proteins_added += 1

	added = orgs_added + proteins_added

	if added == 0:
		print("No new organisms or proteins to add")
	else:
		print("{} new organisms added".format(orgs_added))
		print("{} new proteins added".format(proteins_added))

	# Maybe write new external table
	with open(external_path, 'a') as ext:
		ext_added = 0
		for key in sorted(new_external.keys()):
			ext_added += 1
			ext.write('%s	%s	owl:Class\n' % (new_external[key], key))
	if ext_added > 0:
		print("{} new external classes added".format(ext_added))

def clean_name(name):
	"""Return a tab-replaced name."""
	return name.strip().replace('\t', ' ')

def add_organism(ontie, index, orgs, row, cur):
	"""For each IEDB taxon:
	- add a new_external (if parent is in NCBI Taxonomy, and not yet in external)
	- write a row to index.tsv
	- write a row to organism_map.tsv
	- write a Knotation stanza to ontie.kn"""
	global organism_map, ontie_id, alternative_term, external

	(tax_id, label, rank, parent_tax_id, parents, parent) = row
	if tax_id in organism_map:
		return False

	ontie_id +=1
	curie = 'ONTIE:%07d' % ontie_id
	label = clean_name(label)
	parent = clean_name(parent)
	if rank:
		rank = clean_name(rank)

	# Maybe add a new external class
	if parent_tax_id < 10000000 and not parent in external:
		new_external[parent] = 'NCBITaxon:%d' % parent_tax_id

	index.write('%s	%s	owl:Class		\n' % (curie, label))

	orgs.write('%d	%s	%s\n' % (tax_id, curie, label))

	ontie.write(': %s\n' % curie)
	ontie.write('apply template: taxon class\n')
	ontie.write(' label: %s\n' % label)
	ontie.write(' parent taxon: %s\n' % parent)
	# Maybe add additional parents
	if ',' in parents:
		superclasses = get_superclasses(parent_tax_id_string, parent, cur)
		for sc in superclasses:
			ontie.write('subclass of: %s\n' % sc)
	# Maybe add synonyms
	for alternative_term in alternative_terms[tax_id]:
		ontie.write('alternative term: %s\n' % alternative_term)
	if rank:
		ontie.write('rank: %s\n' % rank)
	ontie.write('\n')

	return True

def add_protein(ontie, index, src, row):
	"""For each IEDB source protein:
	- add a new_external (if organism is in NCBI Taxonomy, and not in external)
	- write a row to index.tsv
	- write a row to source_map.tsv
	- write a Knotation stanza to ontie.kn"""
	global source_map, ontie_id

	(source_id, name, aliases, synonyms, organism_id, organism) = row
	if source_id in source_map:
		return False

	ontie_id +=1
	curie = 'ONTIE:%07d' % ontie_id
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
	
	index.write('%s	%s	owl:Class		\n' % (curie, label))
	
	src.write('%d	%s	%s\n' % (source_id, curie, name))

	ontie.write(': %s\n' % curie)
	ontie.write('apply template: protein class\n')
	ontie.write(' label: %s\n' % name)
	ontie.write(' taxon: %s\n' % organism)
	for alternative_term in alternative_terms:
		alternative_term = alternative_term.strip()
		if alternative_term != '':
			ontie.write('alternative term: %s\n' % alternative_term)
	ontie.write('\n')

	return True

def init_data():
	"""Reads in data from:
	- ontology/index.tsv to get the last ONTIE ID
	- ontology/externals.tsv to get existing external classes
	- organism_map and source_map.tsv to get recently added IDs"""
	global ontie_id, organism_map, external

	if os.path.exists(index_path):
		with open(index_path, 'r') as index:
			lines = index.readlines()
			last = lines[-1]
			curie = last.split('\t')[0]
			last_id = curie.replace('ONTIE:','').lstrip('0')
			ontie_id = int(last_id)
	else:
		with open(index_path, 'w') as index:
			index.write('CURIE	label	type	obsolete	replacement\n')

	if os.path.exists(external_path):
		with open(external_path, 'r') as ext:
			for line in ext:
				(curie, label, rdf_type) = line.split('\t')
				external[label] = curie

	if os.path.exists(organism_map_path):
		with open(organism_map_path, 'r') as orgs:
			next(orgs)
			for line in orgs:
				(tax_id, curie, label) = line.split('\t')
				organism_map[int(tax_id)] = curie
	else:
		with open(organism_map_path, 'w') as orgs:
			orgs.write('TAX_ID	CURIE	LABEL\n')

	if os.path.exists(source_map_path):
		with open(source_map_path, 'r') as src:
			next(src)
			for line in src:
				(tax_id, curie, label) = line.split('\t')
				source_map[int(tax_id)] = curie
	else:
		with open(source_map_path, 'w') as src:
			src.write('SOURCE_ID	CURIE	NAME\n')

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
