CREATE TABLE IF NOT EXISTS prefix (
  prefix TEXT PRIMARY KEY,
  base TEXT NOT NULL
);

INSERT OR IGNORE INTO prefix VALUES
('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'),
('rdfs', 'http://www.w3.org/2000/01/rdf-schema#'),
('xsd', 'http://www.w3.org/2001/XMLSchema#'),
('owl', 'http://www.w3.org/2002/07/owl#'),
('oio', 'http://www.geneontology.org/formats/oboInOwl#'),
('dce', 'http://purl.org/dc/elements/1.1/'),
('dct', 'http://purl.org/dc/terms/'),
('foaf', 'http://xmlns.com/foaf/0.1/'),

('BFO',       'http://purl.obolibrary.org/obo/BFO_'),
('COB',       'http://purl.obolibrary.org/obo/COB_'),
('DOID',      'http://purl.obolibrary.org/obo/DOID_'),
('IAO',       'http://purl.obolibrary.org/obo/IAO_'),
('NCBITaxon', 'http://purl.obolibrary.org/obo/NCBITaxon_'),
('ncbi',      'http://purl.obolibrary.org/obo/ncbitaxon#'),
('OBI',       'http://purl.obolibrary.org/obo/OBI_'),
('PR',        'http://purl.obolibrary.org/obo/PR_'),

('obo',       'http://purl.obolibrary.org/obo/'),

('ONTIE', 'https://ontology.iedb.org/ontology/ONTIE_'),
('IEDB', 'http://iedb.org/');
