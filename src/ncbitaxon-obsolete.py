#!/usr/bin/env python3

import argparse

def main():
  parser = argparse.ArgumentParser(
      description='Create a Turtle file with obsolete NCBI Taxonomy classes')
  parser.add_argument('delnodes_dmp',
      type=argparse.FileType('r'),
      help='the table of merged nodes')
  parser.add_argument('obsolete_ttl',
      type=str,
      help='the Turtle file to write')
  args = parser.parse_args()

  with open(args.obsolete_ttl, 'w') as w:
    w.write('''@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix NCBITaxon: <http://purl.obolibrary.org/obo/NCBITaxon_> .

''')
    for line in args.delnodes_dmp:
      taxid = line.strip().strip('|').strip()
      w.write('NCBITaxon:%s\n' % taxid)
      w.write('  rdf:type owl:Class ;\n')
      w.write('  rdfs:label "obsolete taxon %s" ;\n' % taxid)
      w.write('  owl:deprecated "true"^^xsd:boolean .\n\n')

if __name__ == "__main__":
  main()
