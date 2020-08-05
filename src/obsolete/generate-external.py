#!/usr/bin/env python3

import os, collections
import cx_Oracle

external_path = 'ontology/external.tsv'
manual_external = 'ontology/external_manual.tsv'
external = {}

organisms = """
SELECT o1.organism_id,
	o1.parent_tax_id AS parent,
	o2.organism_name AS parent_name
FROM organism o1, organism o2
WHERE o1.organism_id >= 10000000
	AND o1.parent_tax_id < 10000000
	AND o1.parent_tax_id = o2.organism_id
ORDER BY o1.organism_id
"""

proteins = """
SELECT iri,
	organism_id AS parent,
	organism_name AS parent_name
FROM source
where database = 'IEDB'
"""

def main():
	""""""
	# Connect to the Oracle DB
	conn = cx_Oracle.connect(os.environ['ORACLE_CONN'])
	print("Connecting: {}".format(os.environ['ORACLE_CONN']))
	cur = conn.cursor()

	external = {}

	cur.execute(organisms)
	for row in cur:
		(organism_id, parent, parent_name) = row
		parent_id = 'NCBITaxon:%d' % parent
		external[parent_name] = parent_id

	cur.execute(proteins)
	for row in cur:
		(iri, parent, parent_name) = row
		if parent is None:
			continue
		parent_id = 'NCBITaxon:%d' % parent
		external[parent_name] = parent_id

	with open(external_path, 'w') as ext:
		# Add header
		ext.write('label	CURIE	type\n')
		with open(manual_external, 'r') as man:
			for line in man.readlines():
				ext.write(line)
		for key in sorted(external.keys()):
			ext.write('%s	%s	owl:Class\n' % (key, external[key]))

if __name__ == '__main__':
	main()
