# IEDB Source of Truth

SoT is a system for dynamically creating, maintaining, and sharing an application ontology that builds on multiple reference resources. A reference resource could be a reference ontology such as OBI, or a similar non-ontological resource such as UniProt. We intend for the SoT system to be general, but the primary goal is to serve projects at LJI, including IEDB, LabKey database for HIPC and DORAS, TopCat, and Bioinformatics Core.

The core of SoT is an application ontology (ONTIE) with its own terms and axioms. ONTIE builds on reference resources including NCBI Taxonomy, MRO, OBI, UniProt, and GenPept. We reuse terms from reference resources as much as possible, but when this is not possible we add terms to ONTIE. Examples include taxa not in NCBI Taxonomy, and proteins not in GenPept. New terms can be added to ONTIE immediately, and will be maintained indefinitely. However, if a better term is found in a reference ontology, the ONTIE term will be marked obsolete and mapped to the reference term.

Each reference resource is pulled in and validated using an importer module. Specific versions of reference resources are used, and updates to reference resources are carefully checked for terms that have been dropped, added, merged, or had their logic changed.

Users can search, browse, and query SoT (i.e. the union of ONTIE and the reference resources) using a uniform web-based interface and API. 

SoT consumers such as IEDB will usually have their own internal identifiers for terms, but must keep track of the IRIs for the terms they use from SoT. They can then query SoT using IRIs, ask whether the IRIs have been mapped to new IRIs, and get tables of data for those terms. Consumers can send their users to SoT to find and request terms, but the consumer is responsible for maintaining and displaying terms, local versions of labels and synonyms, and tree structure.

SoT is public and does not contain secret or confidential information. Unauthenticated users can browse and search for terms. Authenticated users can request new terms by selecting a term template and filling in the required information. If SoT can validate that information, it immediately creates a new ONTIE term and provides the user with the new IRI.

A secondary goal of SoT is to demonstrate tight integration across OBO Foundry ontologies. We intend for ONTIE to have a single, integrated and logically-consistent hierarchy, with a unified set of OWL annotation properties and object properties. The term creation and management aspect of SoT may also serve as a good example of how term request can percolate up from specific use-cases to community reference ontologies, while keeping the originating application ontology and annotated datasets in sync.
