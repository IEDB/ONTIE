# API

The IEDB SoT is designed to be used by both humans and software. For humans, we provide HTML pages connected by hyperlinks. For machines, we provide a consistent API to access data in machine-readable formats.

SoT provides access to the ONTIE application ontology and a number of other resources used by ONTIE and IEDB. You can browse the resources, fetch them with the REST API described below, or download them as OWL files or TSV.

Individual terms can be accessed at their term IRI, for example [https://ontology.iedb.org/ontology/ONTIE_0000001](/ontology/ONTIE_0000001). An HTTP GET request to the term IRI will return HTML or JSON-LD representations.

## JSON-LD

The [JSON Linked Data](https://json-ld.org) representation of a single term is a standard JSON object with a few special conventions. For example, [https://ontology.iedb.org/ontology/ONTIE_0000001.json](/ontology/ONTIE_0000001.json) returns this result:

```json
{
  "@context": {
    "IAO": {
      "@id": "http://purl.obolibrary.org/obo/IAO_",
      "@prefix": true
    },
    "NCBITaxon": {
      "@id": "http://purl.obolibrary.org/obo/NCBITaxon_",
      "@prefix": true
    },
    "ONTIE": {
      "@id": "https://ontology.iedb.org/ontology/ONTIE_",
      "@prefix": true
    },
    "ncbi": {
      "@id": "http://purl.obolibrary.org/obo/ncbitaxon#",
      "@prefix": true
    },
    "owl": {
      "@id": "http://www.w3.org/2002/07/owl#",
      "@prefix": true
    },
    "rdf": {
      "@id": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
      "@prefix": true
    },
    "rdfs": {
      "@id": "http://www.w3.org/2000/01/rdf-schema#",
      "@prefix": true
    },
    "rdf:type": {
      "@type": "@id"
    },
    "rdfs:subClassOf": {
      "@type": "@id"
    }
  },
  "@id": "ONTIE:0000001",
  "ONTIE:0003259": "taxon",
  "rdfs:label": "Mus musculus BALB/c",
  "ncbi:has_rank": {
    "@id": "NCBITaxon:subspecies"
  },
  "IAO:0000234": "IEDB",
  "IAO:0000118": "balb",
  "rdfs:subClassOf": "NCBITaxon:10090",
  "rdf:type": "owl:Class"
}
```

## Tables

You can also view and search the resources as tables, using [LDTab](https://github.com/ontodev/ldtab) format. Pages can be downloaded in TSV, CSV, and JSON formats.
