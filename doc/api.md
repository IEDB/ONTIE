---
title: IEDB SoT API
---

# API

The IEDB SoT is designed to be used by both humans and software. For humans, we provide HTML pages connected by hyperlinks. For machines, we provide a consistent API to access data in several machine-readable formats.


## ONTIE and Other Resources

SoT provides access to the ONTIE application ontology and a number of other resources used by ONTIE and IEDB, including the NCBI Taxonomy, Chemical Entities of Biological Interest, the MHC Restriction Ontology, and more. The full list of resources (including ONTIE) is available at [https://ontology.iedb.org/resources](/resources). You can query for a specific resource or across all resources.

- ONTIE: [https://ontology.iedb.org/resources/ONTIE](/resources/ONTIE)
- NCBI Taxonomy: [https://ontology.iedb.org/resources/NCBITaxonomy](/resources/NCBITaxonomy)
- all resources: [https://ontology.iedb.org/resources/all](/resources/all)
- ONTIE (alternative): [https://ontology.iedb.org/ontology/ONTIE](/ontology/ONTIE)


## Individual ONTIE Terms

Individual ONTIE terms can be accessed at their term IRI, for example [https://ontology.iedb.org/ontology/ONTIE_0000001](/ontology/ONTIE_0000001). An HTTP GET request to the term IRI will return an HTML document with embedded [RDFa](https://rdfa.info) data. Alternative representations are available in [Turtle](https://www.w3.org/TeamSubmission/turtle/), [JSON-LD](https://json-ld.org), and TSV formats.


### JSON-LD

The JSON Linked Data representation of a single term is a standard JSON object with a few special conventions:

- the `@context` helps map values to an RDF representation, but can be ignored for many use cases
- `@id` keys are used for CURIE values
- `iri` keys are used for full IRI values
- `label` keys are used for the human-readable label associated with an IRI
- `@value` keys provide the string representations of RDF literals

<!-- GET TEST -->
In order to capture RDF semantics, IRIs and literal values are represented as objects, using arrays when multiple values are given. For example, [https://ontology.iedb.org/ontology/ONTIE_0000001.json?select=label,alternative%20term,subclass%20of](/ontology/ONTIE_0000001.json?select=label,alternative%20term,subclass%20of) includes the following plus JSON-LD context:

```
{"@id": "https://ontology.iedb.org/ontology/ONTIE_0000001",
 "@type": "owl:Class",
 "obo:IAO_0000118": "balb",
 "rdfs:label": "Mus musculus BALB/c",
 "rdfs:subClassOf": {
    "@id": "obo:NCBITaxon_10090"
 }
}
```
<!-- END GET TEST -->

### Tab-Separated Values
<!-- GET TEST -->
A table of tab-separated values about a term can also be requested. By default, the properties included are `IRI`, `label`, `obsolete`, and `replacement`. For example [https://ontology.iedb.org/ontology/ONTIE_0000001.tsv](/ontology/ONTIE_0000001.tsv):

```
IRI	label	obsolete	replacement	recognized
https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c			true
```
<!-- END GET TEST -->
<!-- GET TEST -->
If the query parameter `show-headers` is `false`, then the header row is omitted, for example [https://ontology.iedb.org/ontology/ONTIE_0000001.tsv?show-headers=false](/ontology/ONTIE_0000001.tsv?show-headers=false):

```
https://ontology.iedb.org/ontology/ONTIE_0000001	Mus musculus BALB/c			true
```
<!-- END GET TEST -->
<!-- GET TEST -->
The `select` query parameter controls the columns that are returned. Provide a comma-separated list of predicate labels, or one of the special values: `IRI`, `CURIE`, `recognized`. The order of predicates is respected in the returned data. For example, [https://ontology.iedb.org/ontology/ONTIE_0000008.tsv?select=CURIE,label,alternative%20term](/ontology/ONTIE_0000008.tsv?select=CURIE,label,alternative%20term):

```
CURIE	label	alternative term
ONTIE:0000008	Mus musculus 6.5 TCR Tg	14.3.d|SFERFEIFPKE-specific TCR Tg|Tg(Tcra/Tcrb)1Vbo
```
<!-- END GET TEST -->
Multiple values, such as multiple `alternative term` values, are separated by a single pipe character (`|`).
<!-- GET TEST -->
When `compact=true` is set, values will be returned as CURIEs instead of IRIs, for example [https://ontology.iedb.org/ontology/ONTIE_0002059.tsv?select=CURIE,replacement&compact=true](/ontology/ONTIE_0002059.tsv?select=CURIE,replacement&compact=true):

```
CURIE	replacement
ONTIE:0002059	ONTIE:0002053
```
<!-- END GET TEST -->
<!-- GET TEST -->
If the name of a predicate in a `select` is followed by `[IRI]`, `[CURIE]`, or `[label]`, then the system will attempt to return values for the column in the format. For example: [https://ontology.iedb.org/ontology/ONTIE_0002059.tsv?select=CURIE,replacement%20\[CURIE\],replacement%20\[label\]](/ontology/ONTIE_0002059.tsv?select=CURIE,replacement%20[CURIE],replacement%20[label]):

```
CURIE	replacement [CURIE]	replacement [label]
ONTIE:0002059	ONTIE:0002053	Large structural phosphoprotein (Human betaherpesvirus 5)
```
<!-- END GET TEST -->

## Individual Subjects

You can query for individual subjects within a resource or across all resources using the subject CURIE or IRI. Special characters in IRIs should be escaped:

- [https://ontology.iedb.org/resources/ONTIE/subject?curie=ONTIE:0000001](/resources/ONTIE/subject?curie=ONTIE:0000001)
- [https://ontology.iedb.org/resources/all/subject?curie=ONTIE:0000001](/resources/all/subject?curie=ONTIE:0000001)
- [https://ontology.iedb.org/resources/ONTIE/subject?iri=https%3A%2F%2Fontology.iedb.org%2Fontology%2FONTIE_0000001](/resources/ONTIE/subject?iri=https%3A%2F%2Fontology.iedb.org%2Fontology%2FONTIE_0000001)
- [https://ontology.iedb.org/resources/all/subject?iri=https%3A%2F%2Fontology.iedb.org%2Fontology%2FONTIE_0000001](/resources/all/subject?iri=https%3A%2F%2Fontology.iedb.org%2Fontology%2FONTIE_0000001)

Subject pages are also available in other formats:

- Turtle [https://ontology.iedb.org/resources/ONTIE/subject?curie=ONTIE:0000001&format=ttl](/resources/ONTIE/subject?curie=ONTIE:0000001&format=ttl)
- JSON-LD [https://ontology.iedb.org/resources/ONTIE/subject?curie=ONTIE:0000001&format=json](/resources/ONTIE/subject?curie=ONTIE:0000001&format=json)
- TSV [https://ontology.iedb.org/resources/ONTIE/subject?curie=ONTIE:0000001&format=tsv](/resources/ONTIE/subject?curie=ONTIE:0000001&format=tsv)


## Predicates

You can get the list of all predicates used within a resource or across all resources:

- [https://ontology.iedb.org/resources/ONTIE/predicates](/resources/ONTIE/predicates)
- [https://ontology.iedb.org/resources/all/predicates](/resources/all/predicates)


## Multiple Subjects

You can also query for multiple subjects within a resource or across resources:

- [https://ontology.iedb.org/resources/ONTIE/subjects](/resources/ONTIE/subjects)
- [https://ontology.iedb.org/resources/all/subjects](/resources/all/subjects)

The HTML form lets you build a query and return results in HTML or TSV formats. The query is controlled by the query parameters in the URL.

- `format` can be `html` (default) or `tsv`
- `select` a comma-separated list of predicates to be used as columns in the resulting table; the default is `IRI,label,obsolete,replacement`
- `limit` the number of results to return, defaults to 100, maximum 10000
- `offset` the index of the first result to return
- `show-headers` when `false`, headers will not be included in TSV output
- `compact` when `true` CURIEs will be used instead of IRIs whenever possible

You can specify a constraint on the query as the combination of a predicate, an operator, and an object. The predicate should be a label such as `type` or `alternative term`. The operator should be one of:

- `eq.` for string equality of the object literal
- `like.` for wildcard matching to the literal object, where `*` is the wildcard characters
- `iri.eq.` for string equality of the object IRI
- `iri.like.` for wildcard matching to the object IRI

The object is the value to match. For example, to match any `rdfs:label` starting with 'Mus' the query parameter would be `label=like.Mus*`: [https://ontology.iedb.org/resources/ONTIE/subjects?label=like.Mus*](/resources/ONTIE/subjects?label=like.Mus*)

The `IRI` and `CURIE` query parameters are used to specify exactly which subjects to search for. A row is returned for each requested subject, in order, whether or not the requested subject is found in the resource. This is useful for checking term status. Use the `in.(*)` operator, like so: [https://ontology.iedb.org/resources/ONTIE/subjects?CURIE=in.(ONTIE:0000001,ONTIE:0000002)](/resources/ONTIE/subjects?CURIE=in.%28ONTIE:0000001,ONTIE:0000002%29). Also see "POST instead of GET" below.


## POST instead of GET
<!-- POST TEST -->
When requesting a large number of terms, you can use HTTP POST instead of HTTP GET, and provide a list of the requested CURIEs or IRIs in the body of the request. For example, POSTing to [https://ontology.iedb.org/resources/all/subjects?method=GET&format=tsv](/resources/all/subjects?format=tsv) with this body:

```
CURIE
ONTIE:0000001
NCBITaxon:10090
NCBITaxon:0
```

will return a table:

```
CURIE	label	obsolete	replacement	recognized
ONTIE:0000001	Mus musculus BALB/c			true
NCBITaxon:10090	Mus musculus			true
NCBITaxon:0				false	
```
<!-- END POST TEST -->
The body of the POST request is a list of CURIEs or IRIs. The first row should be `CURIE` or `IRI`. The HTTP `Content-Type` should be `text/plain` or `text/tab-separated-values`, not `application/x-www-form-urlencoded` which is the default for some tools.

The response will be a table of tab-separated values with four columns and a row for each submitted CURIE/IRI. If a term does not exist, no row will be returned for that term. The columns are:

1. IRI or CURIE (corresponding to the request)
2. label
4. obsolete: true if the term is obsolete, blank or false if the term is not obsolete
5. replacement: if the term is recognized and obsolete and has been replaced by another term, this column will contain the replacement term IRI; otherwise it will be blank

You can use the following query parameters in a POST request:
* `show-headers`
* `select` (for predicates)

<!-- POST TEST -->
For example, POSTing to [https://ontology.iedb.org/resources/all/subjects?method=GET&format=tsv&select=CURIE,label&show-headers=false](/resources/all/subjects?format=tsv&select=CURIE,label&show-headers=false) with this body:

```
CURIE
ONTIE:0000001
ONTIE:0000002
```

will return a table:

```
ONTIE:0000001	Mus musculus BALB/c
ONTIE:0000002	Mus musculus BALB/c A2/Kb Tg
```
<!-- END POST TEST -->
