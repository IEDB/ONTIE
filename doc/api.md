---
title: IEDB SoT API
---

# API

The IEDB SoT is designed to be used by both humans and software. For humans, we provide HTML pages connected by hyperlinks. For machines, we provide a consistent API to access data in several machine-readable formats.


## Individual ONTIE Terms

Individual ONTIE terms can be accessed at their term IRI, for example [https://ontology.iedb.org/ontology/ONTIE_0000001](/ontology/ONTIE_0000001). An HTTP GET request to the term IRI will return an HTML document with embedded [RDFa](https://rdfa.info) data. Alternative representations are available in [Turtle](https://www.w3.org/TeamSubmission/turtle/), [JSON-LD](https://json-ld.org), and TSV formats.


### JSON-LD

The JSON Linked Data representation of an ONTIE term is a standard JSON object with a few special conventions:

- the `@context` helps map values to an RDF representation, but can be ignored for many use cases
- `@id` keys are used for CURIE values
- `iri` keys are used for full IRI values
- `label` keys are used for the human-readable label associated with an IRI
- `@value` keys provide the string representations of RDF literals

In order to capture RDF semantics, IRIs and literal values are represented as objects, using arrays when multiple values are given. For example, [https://ontology.iedb.org/ontology/ONTIE_0000001.json](/ontology/ONTIE_0000001.json) includes the following:

```
{"label": {"@value":"Mus musculus BALB/c"},
 "alternative term": [{"@value":"balb"}],
 "parent taxon":
 {"@id": "NCBITaxon:10090",
  "iri": "http://purl.obolibrary.org/obo/NCBITaxon_10090",
  "label": "Mus musculus"}
 ...}
```


### Tab-Separated Values

A table of tab-separated values about a term can also be requested. By default, five columns of data are provided, for example [https://ontology.iedb.org/ontology/ONTIE_0000001.tsv](/ontology/ONTIE_0000001.tsv):

```
IRI	label	recognized	obsolete	replacement
https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c	true		
```

The `select` query parameter controls the columns that are returned. Provide a comma-separated list of predicate labels, or one of the special values: `IRI`, `CURIE`, `recognized`. The order of predicates is respected in the returned data. For example, [https://ontology.iedb.org/ontology/ONTIE_0000008.tsv?select=CURIE,label,alternative%20term](/ontology/ONTIE_0000008.tsv?select=CURIE,label,alternative%20term):

```
CURIE	label	alternative term
ONTIE:0000008	Mus musculus 6.5 TCR Tg	14.3.d|SFERFEIFPKE-specific TCR Tg|Tg(Tcra/Tcrb)1Vbo
```

Multiple values, such as multiple `alternative term` values, are separated by a single pipe character (`|`).

When `compact=true` is set, values will be returned as CURIEs instead of IRIs, for example [https://ontology.iedb.org/ontology/ONTIE_0002059.tsv?select=CURIE,replacement&compact=true](/ontology/ONTIE_0002059.tsv?select=CURIE,replacement&compact=true):

```
CURIE	replacement
ONTIE:0002059	ONTIE:0002053
```


## Multiple Ontology Terms

Information about multiple ontology terms can be retrieved at these IRIs:

- [https://ontology.iedb.org/ontology/](/ontology/)
- [https://ontology.iedb.org/ontology/ONTIE](/ontology/ONTIE)

The `format` query parameter can be used to select between `html`, `ttl`, `json`, and `tsv` formats. For TSV, the `select` and `compact` query parameters can be used, as above. For any of the formats, `CURIE` and `IRI` query parameters can be set to include either one term or multiple terms:

- For a single term, use the equality operator `eq.`, for example [https://ontology.iedb.org/ontology/?CURIE=eq.ONTIE:0000001](/ontology/?CURIE=eq.ONTIE:0000001).
- For multiple terms, use the `in.` operator and provide a space-separated list: [https://ontology.iedb.org/ontology/?CURIE=in.ONTIE:0000001%20ONTIE:0000002](/ontology/?CURIE=in.ONTIE:0000001%20ONTIE:0000002)


### POST instead of GET

When requesting a large number of terms, you can use HTTP POST instead of HTTP GET, and provide a list of the requested CURIEs or IRIs in the body of the request. For this to work, you MUST include `method=GET` in the query string. For example, POSTing to [https://ontology.iedb.org/ontology/?method=GET&format=tsv](/ontology/?method=GET&format=tsv) with this body:

```
CURIE
ONTIE:0000001
ONTIE:0000002
```

will return a table:

```
IRI	label	recognized	obsolete	replacement
https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c	true		
https://ontology.iedb.org/ontology/ONTIE_0000002	Mus musculus BALB/c A2/Kb Tg	true		
```

The body of the POST request is a list of CURIEs or IRIs. The first row should be `CURIE` or `IRI`.


### Example: Term Status

When requesting a TSV table, the default columns provide a summary of each term's status. For example, POST to [https://ontology.iedb.org/ontology/?method=GET&format=tsv](/ontology/?method=GET&format=tsv) with this body:

```
CURIE
ONTIE:0000001
NCBITaxon:10090
NCBITaxon:12
NCBITaxon:3
NCBITaxon:0
```

The response will be a table of tab-separated values with four columns and a row for each submitted IRI. The columns are:

1. IRI or CURIE (corresponding to the request)
2. label
3. recognized: true if the term is available anywhere in SoT, false otherwise
4. obsolete: true if the term is obsolete, blank or false if the term is not obsolete
5. replacement: if the term is recognized and obsolete and has been replaced by another term, this column will contain the replacement term IRI; otherwise it will be blank

For example (contains tab characters):

```
CURIE	label	recognized	obsolete	replacement
ONTIE:0000001	Mus musculus BALB/c	true		
NCBITaxon:10090	Mus musculus	true		
NCBITaxon:12	obsolete taxon 12	true	true	http://purl.obolibrary.org/obo/NCBITaxon_74109
NCBITaxon:3	obsolete taxon 3	true	true	
NCBITaxon:0		false		
```


