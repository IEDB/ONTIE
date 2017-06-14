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

# Paths
index_path = 'ontology/index.tsv'
external_path = 'ontology/external.tsv'
organism_map_path = 'organism_map.tsv'
source_map_path = 'source_map.tsv'

# Dictionaries from internal ID to curie
organism_map = {}
source_map = {}

# Dictionaries from NCBI Taxon labels to CURIEs
external = {}
new_external = {}

# A dictionary from tax_id to a list of synonyms.
alternative_terms = collections.defaultdict(list)


## Read current data or initialize tables

if os.path.exists(index_path):
  with open(index_path, 'r') as index:
    lines = index.readlines()
    last = lines[-1]
    (curie, label, rdf_type, obsolete, relacement) = last.split('\t')
    last_id = curie.replace('ONTIE:','').lstrip('0')
    ontie_id = int(last_id)
else:
  with open(index_path, 'w') as index:
    index.write('CURIE	label	type	obsolete	replacement\n')

if os.path.exists(external_path):
  with open(external_path, 'r') as ext:
    next(ext)
    for line in ext:
      (label, curie, rdf_type) = line.split('\t')
      external[label] = curie
#else:
#  ext.write('label	target	type\n')
#  ext.write('label	rdfs:label	owl:AnnotationProperty\n')
#  ext.write('type	rdf:type > link	rdf:Property\n')
#  ext.write('subclass of	rdfs:subClassOf > link	rdf:Property\n')
#  ext.write('obsolete	owl:deprecated > xsd:boolean	owl:DatatypeProperty\n')
#  ext.write('alternative term	obo:IAO_0000118	owl:AnnotationProperty\n')
#  ext.write('IEDB alternative term	obo:OBI_9991118	owl:AnnotationProperty\n')
#  ext.write('rank	ncbitaxon:has_rank > link	owl:AnnotationProperty\n')
#  ext.write('in taxon	obo:RO_0002162 > link	owl:ObjectProperty\n')
#  ext.write('subspecies	NCBITaxon:subspecies	owl:Class\n')
#  ext.write('no rank	NCBITaxon:no_rank	owl:Class\n')
#  ext.write('protein	obo:PR_000000001	owl:Class\n')

if os.path.exists(organism_map_path):
  with open(organism_map_path, 'r') as orgs:
    next(orgs)
    for line in orgs:
      (tax_id, curie, label) = line.split('\t')
      organism_map[int(tax_id)] = curie
else:
  with open(organism_map_path, 'w') as index:
    orgs.write('TAX_ID	CURIE	LABEL\n')

if os.path.exists(source_map_path):
  with open(source_map_path, 'r') as sources:
    next(sources)
    for line in sources:
      (tax_id, curie, label) = line.split('\t')
      source_map[int(tax_id)] = curie
else:
  with open(source_map_path, 'w') as sourceds:
    sources.write('SOURCE_ID	CURIE	NAME\n')


## Organisms

def clean_name(name):
  return name.strip().replace('\t', ' ')

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
  o2.organism_name AS parent
FROM organism o1, organism o2
WHERE o1.parent_tax_id = o2.organism_id
  AND o1.organism_id >= 10000000
ORDER BY o1.organism_id
"""

def add_organism(ontie, index, orgs, row):
  """For each IEDB taxon:
  - add an new_external (if parent is in NCBI Taxonomy, and not yet in external)
  - write a row to index.tsv
  - write a row to organism_map.tsv
  - write a Knotation stanza to ontie.kn"""
  global organism_map, ontie_id, alternative_term, external

  (tax_id, label, rank, parent_tax_id, parent) = row
  if tax_id in organism_map:
    return

  ontie_id +=1
  curie = 'ONTIE:%07d' % ontie_id
  label = clean_name(label)
  parent = clean_name(parent)
  if rank:
    rank = clean_name(rank)

  if parent_tax_id < 10000000 and not parent in external:
    new_external[parent] = 'NCBITaxon:%d' % parent_tax_id

  index.write('%s	%s	owl:Class	false	\n' % (curie, label))

  orgs.write('%d	%s	%s\n' % (tax_id, curie, label))

  ontie.write(': %s\n' % curie)
  ontie.write('template: taxon class\n')
  ontie.write('label: %s\n' % label)
  for alternative_term in alternative_terms[tax_id]:
    ontie.write('alternative term: %s\n' % alternative_term)
  ontie.write('parent taxon: %s\n' % parent)
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
ORDER BY source_id
"""

def add_protein(ontie, index, sources, row):
  """For each IEDB SRC protein:
  - add an external.tsv entry (if organism is in NCBI Taxonomy)
  - write a row to index.tsv
  - write a row to source_map.tsv
  - write a Knotation stanza to ontie.kn"""
  global source_map, ontie_id, external

  (source_id, name, aliases, synonyms, organism_id, organism) = row
  if source_id in source_map:
    return

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

  if organism_id < 10000000 and not organism in external:
    new_external[organism] = 'NCBITaxon:%d' % organism_id

  index.write('%s	%s	owl:Class	false	\n' % (curie, label))

  sources.write('%d	%s	%s\n' % (source_id, curie, name))

  ontie.write(': %s\n' % curie)
  ontie.write('template: protein class\n')
  ontie.write('protein label: %s\n' % name)
  ontie.write('protein taxon: %s\n' % organism)
  for alternative_term in alternative_terms:
    alternative_term = alternative_term.strip()
    if alternative_term != '':
      ontie.write('alternative term: %s\n' % alternative_term)
  ontie.write('\n')


## Add organisms and proteins

conn = cx_Oracle.connect(os.environ['ORACLE_CONN'])
cur = conn.cursor()

# Collect alternative terms
cur.execute(synonyms)
for row in cur:
  (tax_id, name) = row
  alternative_terms[tax_id].append(name.strip())

with open('ontology/ontie.kn', 'a') as ontie:
  with open(index_path, 'a') as index:
    with open(organism_map_path, 'a') as orgs:
      cur.execute(organisms)
      for row in cur:
        add_organism(ontie, index, orgs, row)
    with open(organism_map_path, 'a') as sources:
      cur.execute(proteins)
      for row in cur:
        add_protein(ontie, index, sources, row)


## Write External Table

with open('ontology/external.tsv', 'a') as ext:
  for key in sorted(new_external.keys()):
    ext.write('%s	%s	owl:Class\n' % (key, new_external[key]))
