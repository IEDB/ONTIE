CREATE TABLE IF NOT EXISTS prefix (
  prefix TEXT PRIMARY KEY,
  base TEXT NOT NULL
);

INSERT OR IGNORE INTO prefix VALUES
("rdf", "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
("rdfs", "http://www.w3.org/2000/01/rdf-schema#"),
("xsd", "http://www.w3.org/2001/XMLSchema#"),
("owl", "http://www.w3.org/2002/07/owl#"),
("oio", "http://www.geneontology.org/formats/oboInOwl#"),
("dce", "http://purl.org/dc/elements/1.1/"),
("dct", "http://purl.org/dc/terms/"),
("foaf", "http://xmlns.com/foaf/0.1/"),

("BFO",       "http://purl.obolibrary.org/obo/BFO_"),
("COB",       "http://purl.obolibrary.org/obo/COB_"),
("DOID",      "http://purl.obolibrary.org/obo/DOID_"),
("IAO",       "http://purl.obolibrary.org/obo/IAO_"),
("NCBITaxon", "http://purl.obolibrary.org/obo/NCBITaxon_"),
("ncbi",      "http://purl.obolibrary.org/obo/ncbitaxon#"),
("OBI",       "http://purl.obolibrary.org/obo/OBI_"),
("PR",        "http://purl.obolibrary.org/obo/PR_"),

("obo",       "http://purl.obolibrary.org/obo/"),

("ONTIE",         "https://ontology.iedb.org/ontology/ONTIE_"),
("taxon",         "https://ontology.iedb.org/taxon/"),
("taxon_protein", "https://ontology.iedb.org/taxon-protein/"),
("protein",       "https://ontology.iedb.org/protein/"),
("role",          "https://ontology.iedb.org/role/"),
("by_role",       "https://ontology.iedb.org/by-role/"),
("other",         "https://ontology.iedb.org/other/"),
("nonpeptide",    "https://ontology.iedb.org/nonpeptide/"),
("IEDB",          "http://iedb.org/"),

("IUIS",          "http://www.allergen.org/viewallergen.php?aid="),
("uniprot",       "http://www.uniprot.org/uniprot/"),
("annotation",    "http://purl.uniprot.org/annotation/"),
("NCBI",          "https://www.ncbi.nlm.nih.gov/protein/");