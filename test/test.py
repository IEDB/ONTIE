#!/usr/bin/env python3

import argparse, json, difflib

from requests import get, post
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from pprint import pprint

def main():
  parser = argparse.ArgumentParser(
      description='Test IEDB SoT')
  parser.add_argument('root',
      type=str,
      help='the root URL to test')
  args = parser.parse_args()
  root = args.root

  # Test homepage
  res = get(root)
  assert res.status_code == 200
  soup = BeautifulSoup(res.text, 'html.parser')
  assert soup.title.string == 'IEDB Source of Truth'

  # Test subject page
  res = get(root + '/ontology/ONTIE_0000001', headers={'Accept': 'text/html'})
  assert res.status_code == 200
  soup = BeautifulSoup(res.text, 'html.parser')
  assert soup.title.string == 'Mus musculus BALB/c'
  span = soup.find('span', string='Mus musculus BALB/c')
  assert span
  assert span['property'] == 'rdfs:label'
  link = soup.find('a', string='owl:Class')
  assert link
  #assert link['rel'][0] == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type'
  #assert link['resource'] == 'http://www.w3.org/2002/07/owl#Class'
  link = soup.find('a', string='Turtle (ttl)')
  assert link
  link = soup.find('a', string='JSON-LD (json)')
  assert link
  link = soup.find('a', string='TSV (tsv)')
  assert link

  # Test JSON
  res = get(root + '/ontology/ONTIE_0000001.json')
  js = json.loads(res.text)
  #assert js['type'][0]['@id'] == 'owl:Class'
  assert js['label']['@value'] == 'Mus musculus BALB/c'

  # Test Turtle
  res = get(root + '/ontology/ONTIE_0000001.ttl')
  assert 'rdfs:label "Mus musculus BALB/c"' in res.text

  # Test TSV
  res = get(root + '/ontology/ONTIE_0000001.tsv')
  assert res.text == """IRI	label	recognized	obsolete	replacement
https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c	true		
"""
  res = get(root + '/ontology/ONTIE_0000001.tsv?show-headers=false')
  assert res.text == """https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c	true		
"""
  res = get(root + '/ontology/ONTIE_0000008.tsv?select=CURIE,label,alternative%20term')
  assert res.text == """CURIE	label	alternative term
ONTIE:0000008	Mus musculus 6.5 TCR Tg	14.3.d|SFERFEIFPKE-specific TCR Tg|Tg(Tcra/Tcrb)1Vbo
"""
  res = get(root + '/ontology/ONTIE_0002059.tsv?select=CURIE,replacement&compact=true')
  assert res.text == """CURIE	replacement
ONTIE:0002059	ONTIE:0002053
"""
  res = get(root + '/ontology/ONTIE_0002059.tsv?select=CURIE,replacement%20[CURIE],replacement%20[label]')
  assert res.text == """CURIE	replacement [CURIE]	replacement [label]
ONTIE:0002059	ONTIE:0002053	Large structural phosphoprotein (Human betaherpesvirus 5)
"""

  # Test mutliple subjects
  res = get(root + '/ontology/?CURIE=eq.ONTIE:0000001', headers={'Accept': 'text/html'})
  assert res.status_code == 200
  soup = BeautifulSoup(res.text, 'html.parser')
  span = soup.find('span', string='Mus musculus BALB/c')
  assert span
  assert span['property'] == 'rdfs:label'

  res = get(root + '/ontology/?CURIE=in.ONTIE:0000001%20ONTIE:0000002', headers={'Accept': 'text/html'})
  assert res.status_code == 200
  soup = BeautifulSoup(res.text, 'html.parser')
  link = soup.find('a', string='ONTIE:0000001 Mus musculus BALB/c')
  assert link
  assert '/ontology/ONTIE_0000001' in link['href']
  link = soup.find('a', string='ONTIE:0000002 Mus musculus BALB/c A2/Kb Tg')
  assert link
  assert '/ontology/ONTIE_0000002' in link['href']

  # Test POST
  res = post(root + '/ontology/?method=GET&format=tsv', data="""CURIE
ONTIE:0000001
ONTIE:0000002
""")
  assert res.text == """CURIE	label	recognized	obsolete	replacement
ONTIE:0000001	Mus musculus BALB/c	true		
ONTIE:0000002	Mus musculus BALB/c A2/Kb Tg	true		
"""
  res = post(root + '/ontology/?method=GET&format=tsv', data="""CURIE
ONTIE:0000001
NCBITaxon:10090
NCBITaxon:12
NCBITaxon:3
NCBITaxon:0
""")
  assert res.text == """CURIE	label	recognized	obsolete	replacement
ONTIE:0000001	Mus musculus BALB/c	true		
NCBITaxon:10090	Mus musculus|mouse	true		
NCBITaxon:12	obsolete taxon 12	true	true	http://purl.obolibrary.org/obo/NCBITaxon_74109
NCBITaxon:3	obsolete taxon 3	true	true	
NCBITaxon:0		false		
"""


if __name__ == "__main__":
  main()

