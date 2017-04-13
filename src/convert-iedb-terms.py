#!/usr/bin/env python3
#
# Query IEDB's Oracle curation database
# for IEDB taxa and SRC proteins
# then generate a Knotation representation
# with mapping and context files to support it.
#
# Requires cx_Oracle module
# https://gist.github.com/rmoff/5a70862f27d2284e9541
#
# Set ORACLE_CONN environment variable.

import os, collections
import cx_Oracle

## Globals

# ONTIE ID counter
ontie_id = 0

# A dictionary from NCBI Taxon CURIEs to their labels
external = {}

# A dictionary from tax_id to a list of synonyms.
alternative_terms = collections.defaultdict(list)


## Organisms

def clean_name(name):
  return name.strip().replace('\t', ' ')

synonyms = """
SELECT tax_id, name_txt
FROM names
WHERE name_class = 'synonym'
  AND tax_id >= 10000000
  -- AND tax_id <= 10000003
ORDER BY tax_id
"""

organisms = """
SELECT o1.organism_id,
  o1.organism_name AS label,
  o1.rank,
  o1.parent_tax_id,
  o2.organism_name AS parent
FROM organism o1, organism o2
WHERE o1.parent_tax_id = o2.organism_id
  AND o1.organism_id >= 10000000
  -- AND o1.organism_id <= 10000003
ORDER BY o1.organism_id
"""

def add_organism(ontie, index, orgs, row):
  """For each IEDB taxon:
  - add an external.tsv entry (if parent is in NCBI Taxonomy)
  - write a row to index.tsv
  - write a row to organism_map.tsv
  - write a Knotation stanza to ontie.kn"""
  global ontie_id, alternative_term, external

  ontie_id +=1
  curie = 'ONTIE:%07d' % ontie_id

  (tax_id, label, rank, parent_tax_id, parent) = row
  label = clean_name(label)
  parent = clean_name(parent)
  if rank:
    rank = clean_name(rank)

  if parent_tax_id < 10000000:
    external[parent] = 'NCBITaxon:%d' % parent_tax_id

  index.write('%s	%s	owl:Class	false	\n' % (curie, label))

  orgs.write('%d	%s	%s\n' % (tax_id, curie, label))

  ontie.write(': %s\n' % curie)
  ontie.write('type: owl:Class\n')
  ontie.write('label: %s\n' % label)
  for alternative_term in alternative_terms[tax_id]:
    ontie.write('alternative term: %s\n' % alternative_term)
  ontie.write('subclass of: %s\n' % parent)
  if rank:
    ontie.write('rank: %s\n' % rank)
  ontie.write('\n')


## Proteins

proteins = """
SELECT source_id, name, aliases, synonyms, organism_id, organism_name
FROM source
WHERE database = 'IEDB'
  AND organism_id IS NOT NULL
  AND organism_name IS NOT NULL
  --AND rownum < 100
ORDER BY source_id
"""

def add_protein(ontie, index, sources, row):
  """For each IEDB SRC protein:
  - add an external.tsv entry (if organism is in NCBI Taxonomy)
  - write a row to index.tsv
  - write a row to source_map.tsv
  - write a Knotation stanza to ontie.kn"""
  global ontie_id, external

  ontie_id +=1
  curie = 'ONTIE:%07d' % ontie_id

  (source_id, name, aliases, synonyms, organism_id, organism) = row
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

  if organism_id < 10000000:
    external[organism] = 'NCBITaxon:%d' % organism_id

  index.write('%s	%s	owl:Class	false	\n' % (curie, label))

  sources.write('%d	%s	%s\n' % (source_id, curie, name))

  ontie.write(': %s\n' % curie)
  ontie.write('type: owl:Class\n')
  ontie.write('label: %s\n' % label)
  ontie.write('IEDB alternative term: %s\n' % name)
  for alternative_term in alternative_terms:
    alternative_term = alternative_term.strip()
    if alternative_term != '':
      ontie.write('alternative term: %s\n' % alternative_term)
  ontie.write('subclass of: protein\n')
  ontie.write('in taxon: %s\n' % organism)
  ontie.write('\n')


## Add organisms and proteins

conn = cx_Oracle.connect(os.environ['ORACLE_CONN'])
cur = conn.cursor()

# Collect alternative terms
cur.execute(synonyms)
for row in cur:
  (tax_id, name) = row
  alternative_terms[tax_id].append(name.strip())

with open('ontology/ontie.kn', 'w') as ontie:
  with open('ontology/index.tsv', 'w') as index:
    index.write('CURIE	label	type	obsolete	replacement\n')

    with open('organism_map.tsv', 'w') as orgs:
      orgs.write('TAX_ID	CURIE	LABEL\n')
      cur.execute(organisms)
      for row in cur:
        add_organism(ontie, index, orgs, row)
    with open('source_map.tsv', 'w') as sources:
      sources.write('SOURCE_ID	CURIE	NAME\n')
      cur.execute(proteins)
      for row in cur:
        add_protein(ontie, index, sources, row)


## Write External Table

with open('ontology/external.tsv', 'w') as ext:
  ext.write('label	target	type\n')
  ext.write('label	rdfs:label	owl:AnnotationProperty\n')
  ext.write('type	rdf:type > link	rdf:Property\n')
  ext.write('subclass of	rdfs:subClassOf > link	rdf:Property\n')
  ext.write('obsolete	owl:deprecated > xsd:boolean	owl:DatatypeProperty\n')
  ext.write('alternative term	obo:IAO_0000118	owl:AnnotationProperty\n')
  ext.write('IEDB alternative term	obo:OBI_9991118	owl:AnnotationProperty\n')
  ext.write('rank	ncbitaxon:has_rank > link	owl:AnnotationProperty\n')
  ext.write('in taxon	obo:RO_0002162 > link	owl:ObjectProperty\n')
  ext.write('subspecies	NCBITaxon:subspecies	owl:Class\n')
  ext.write('no rank	NCBITaxon:no_rank	owl:Class\n')
  ext.write('protein	obo:PR_000000001	owl:Class\n')

  for key in sorted(external.keys()):
    ext.write('%s	%s	owl:Class\n' % (key, external[key]))
