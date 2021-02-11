import csv
import gizmos.export
import gizmos.extract
import gizmos.search
import gizmos.tree
import io
import logging
import os
import sqlite3
import subprocess

from flask import abort, Flask, request, Response
from jinja2 import Template


app = Flask(__name__)

resources = {
    "all": "All resources",
    "ONTIE": "Ontology for Immune Epitopes",
    "DOID": "Human Disease Ontology",
    "OBI": "Ontology for Biomedical Investigations",
}


@app.route("/")
def index():
    with open("templates/main.html.jinja2", "r") as f:
        template = Template(f.read())
    return template.render(content="Hello, world!")


@app.route("/ontology/<term_id>.<fmt>", methods=["GET"])
def get_term(term_id, fmt):
    db = get_database("ontie")
    term_id = term_id.replace("_", ":", 1)
    prefixes = get_prefixes(db)

    select = request.args.get("select")
    show_headers = request.args.get("show-headers", "true")
    compact = request.args.get("compact", "false")
    values = "IRI"
    if compact == "true":
        values = "CURIE"

    if select:
        predicates = select.split(",")
    else:
        predicates = [values, "label", "obsolete", "replacement"]

    if fmt == "json":
        export = gizmos.extract.extract_terms(
            db, [term_id], predicates, fmt="json-ld", no_hierarchy=True
        )
        mt = "application/json"
    else:
        if fmt == "tsv":
            mt = "text/tab-separated-values"
        elif fmt == "csv":
            mt = "text/comma-separated-values"
        else:
            abort(400, "Unknown format requested (must be html or tsv): " + fmt)

        no_headers = False
        if show_headers != "true":
            no_headers = True

        if (fmt == "tsv" and not select) or (select and "recognized" in predicates):
            export = export_tsv(
                db, prefixes, values, [term_id], predicates, show_headers=show_headers
            )
        else:
            export = gizmos.export.export_terms(
                db, [term_id], predicates, fmt, no_headers=no_headers, default_value_format=values,
            )

    if not export:
        return "Term not found in database"

    return Response(export, mimetype=mt)


@app.route("/ontology", methods=["GET"])
def tree():
    return get_tree(None)


@app.route("/ontology/<term_id>", methods=["GET"])
def tree_at(term_id):
    return get_tree(term_id)


@app.route("/resources")
def show_all_resources():
    content = """
<div class="row">
    <div class="col-12">
        <h1>Resources</h1>
    </div>
</div>
<div class="row">
    <div class="col-12">
        <ul>"""
    for ns, name in resources.items():
        content += f'<li><a href="resources/{ns}">{name}</a></li>'
    content += "</ul></div></div>"
    with open("templates/main.html.jinja2", "r") as f:
        template = Template(f.read())
    return template.render(content=content)


@app.route("/resources/<resource>")
def show_resource(resource):
    if resource not in resources:
        abort(404, "Resource not found: " + resource)
    content = f"""<h1>{resources[resource]}</h1>
    <ul>
    <li><a href="{resource}/subjects">Subjects</a></li>
    <li><a href="{resource}/predicates">Predicates</a></li>
    </ul>"""
    with open("templates/main.html.jinja2", "r") as f:
        template = Template(f.read())
    return template.render(content=content)


@app.route("/resources/<resource>/<entity_type>", methods=["GET", "POST"])
def show_resource_terms(resource, entity_type):
    if resource not in resources:
        abort(404, "Resource not found: " + resource)
    if entity_type not in ["subjects", "predicates"]:
        abort(400, "Unknown entity type: " + entity_type)

    db = get_database(resource)

    # Get prefixes
    prefixes = get_prefixes(db)

    # Format
    fmt = request.args.get("format", "html")
    if fmt not in ["html", "tsv"]:
        abort(400, "Unknown format requested (must be html or tsv): " + fmt)

    # Show TSV headers
    show_headers_str = request.args.get("show-headers", "true")
    show_headers = True
    if show_headers_str == "false":
        show_headers = False
    # Use CURIEs instead of IRIs
    compact = request.args.get("compact", "false")
    values = "IRI"
    if compact == "true":
        values = "CURIE"

    if request.method == "POST":
        # If request was sent via PURL it may show up in form
        data = request.form.to_dict(flat=False)
        if not data:
            # If request was sent as body, check data
            data = request.data.decode("utf-8")
        else:
            data = list(data.keys())[0]
        subset = []
        for line in data.split("\n"):
            if not line.strip():
                continue
            if line.strip() == "CURIE":
                values = "CURIE"
                continue
            elif line.strip() == "IRI":
                values = "IRI"
                continue
            subset.append(line.strip())
        if values == "IRI":
            subset = get_curies(prefixes, subset)
    else:
        # Constraints
        label_query = request.args.get("label")
        curie_query = request.args.get("curie")

        # Display results
        offset = int(request.args.get("offset", "1")) - 1
        limit = int(request.args.get("limit", "100"))
        next_set = offset + limit + 1
        previous_set = offset - limit
        if previous_set < 0:
            previous_set = 0

        term_ids = []
        with sqlite3.connect(db) as conn:
            cur = conn.cursor()
            if entity_type == "subjects":
                term_ids = get_term_ids(resource, cur, "subject", label_query, curie_query)
                if isinstance(term_ids, str):
                    # Error message
                    return term_ids
            else:
                term_ids = get_term_ids(resource, cur, "predicate", label_query, curie_query)
                if isinstance(term_ids, str):
                    # Error message
                    return term_ids
        subset = term_ids[offset : next_set - 1]

    # A list of predicates
    select = request.args.get("select")
    if select:
        predicates = select.split(",")
    else:
        predicates = [values, "label", "obsolete", "replacement"]

    if fmt == "html":
        content = gizmos.export.export_terms(
            db, subset, predicates, "html", default_value_format=values,
        )
        with open("templates/resource_page.html.jinja2", "r") as f:
            template = Template(f.read())
        return template.render(content=content, previous_set=previous_set, next_set=next_set)

    if select and "recognized" not in predicates:
        # Custom predicates defined
        tsv = gizmos.export.export_terms(
            db, subset, predicates, "tsv", no_headers=not show_headers, default_value_format=values,
        )
    else:
        # No predicates defined, add "recognized"
        tsv = export_tsv(db, prefixes, values, subset, predicates, show_headers=show_headers)
    return Response(tsv, mimetype="text/tab-separated-values")


@app.route("/resources/<resource>/subject", methods=["GET"])
def get_term_from_resource(resource):
    if resource not in resources:
        abort(404, "Resource not found: " + resource)

    db = get_database(resource)

    curie = request.args.get("curie", None)
    iri = request.args.get("iri", None)
    if not curie and not iri:
        abort(400, "A CURIE or IRI is required in URL query parameters")

    if iri:
        with sqlite3.connect(db) as conn:
            cur = conn.cursor()
            cur.execute("SELECT DISTINCT prefix, base FROM prefix")
            for row in cur.fetchall():
                if iri.startswith(row[1]):
                    curie = iri.replace(row[1], row[0] + ":")
        if not curie:
            abort(422, "Cannot process IRI due to unknown namespace: " + iri)

    fmt = request.args.get("format", "html")
    if fmt not in ["html", "json", "tsv", "ttl"]:
        abort(400, "Unknown format requested (must be html, json, tsv): " + fmt)

    if fmt == "html":
        # TODO - do we want table or tree here?
        return gizmos.export.export_terms(db, [curie], None, "html", default_value_format="IRI",)

    if fmt == "json":
        mt = "application/json"
        export = gizmos.extract.extract_terms(db, [curie], None, fmt="json-ld")
    elif fmt == "ttl":
        mt = "text/turtle"
        export = gizmos.extract.extract_terms(db, [curie], None)
    else:
        mt == "text/tab-separated-values"
        export = gizmos.export.export_terms(db, [curie], None, "tsv", default_value_format="IRI")
    return Response(export, mimetype=mt)


def export_tsv(db, prefixes, value_format, subset, predicates, show_headers=True):
    res = gizmos.export.export_terms(
        db, subset, predicates, "tsv", default_value_format=value_format,
    )
    if "CURIE" in predicates:
        identifier = "CURIE"
    elif "IRI" in predicates:
        identifier = "IRI"
    else:
        return res
    reader = csv.DictReader(res.splitlines(), delimiter="\t")
    rows = {}
    for row in reader:
        term = row[identifier]
        if identifier == "IRI":
            term = get_curie(prefixes, term)
            print(term)
        rows[term] = row
    rows_new = []
    for s in subset:
        row = rows.get(s)
        if not row:
            rows_new.append({identifier: s, "recognized": "false"})
        else:
            row["recognized"] = "true"
            rows_new.append(row)
    if "recognized" not in predicates:
        predicates.append("recognized")
    output = io.StringIO()
    writer = csv.DictWriter(output, delimiter="\t", lineterminator="\n", fieldnames=predicates)
    if show_headers:
        writer.writeheader()
    writer.writerows(rows_new)
    return output.getvalue()


def get_curie(prefixes, iri):
    for p, namespace in prefixes.items():
        if iri.startswith(p):
            return iri.replace(p, namespace + ":")
    return f"<{iri}>"


def get_curies(prefixes, iris):
    curies = []
    for iri in iris:
        curies.append(get_curie(prefixes, iri))
    return curies


def get_database(resource):
    db_name = resource.lower()
    db = f"../build/{db_name}.db"
    if not os.path.exists("../build"):
        os.mkdir("../build")
    if not os.path.exists(db):
        # TODO - make database
        logging.info("Building database for " + resource)
        rc = subprocess.call(f"cd .. && make build/{db_name}.db", shell=True)
        if rc != 0:
            return abort(500, description="Unable to create database for " + resource)
    return db


def get_prefixes(db):
    with sqlite3.connect(db) as conn:
        cur = conn.cursor()
        prefixes = {}
        cur.execute("SELECT * FROM prefix")
        for row in cur.fetchall():
            prefixes[row[1]] = row[0]
    prefixes_sorted = {}
    for k in sorted(prefixes, key=len, reverse=True):
        prefixes_sorted[k] = prefixes[k]
    return prefixes_sorted


def get_term_ids(resource, cur, entity_type, label_query, curie_query):
    if label_query:
        query_type = label_query.split(".", 1)[0]
        query = label_query.split(".", 1)[1].replace("*", "%")
        if query_type == "like":
            query = query.replace("*", "%")
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE predicate = 'rdfs:label' AND value LIKE '{query}'"""
            )
        elif query_type == "eq":
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE predicate = 'rdfs:label' AND value = '{query}'"""
            )
        elif query_type == "in":
            select_terms = ", ".join([f"'{x}'" for x in query.lstrip("(").rstrip(")").split(",")])
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE predicate = 'rdfs:label' AND value IN ({select_terms})"""
            )
        else:
            abort(422, "Unable to process 'label' query; bad constraint type: " + query_type)
    elif curie_query:
        query_type = curie_query.split(".", 1)[0]
        query = curie_query.split(".", 1)[1]
        if query_type == "like":
            query = query.replace("*", "%")
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE {entity_type} LIKE '{query}'"""
            )
        elif query_type == "eq":
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE {entity_type} = '{query}'"""
            )
        elif query_type == "in":
            select_terms = ", ".join([f"'{x}'" for x in query.lstrip("(").rstrip(")").split(",")])
            cur.execute(
                f"""SELECT DISTINCT {entity_type} FROM statements
                WHERE {entity_type} IN ({select_terms})"""
            )
        else:
            abort(422, "Unable to process 'label' query; bad constraint type: " + query_type)
    else:
        if entity_type == "subject":
            if resource != "all":
                cur.execute(
                    f"""SELECT DISTINCT subject FROM statements
                    WHERE predicate = 'rdf:type' AND object = 'owl:Class'
                    AND subject LIKE '{resource}:%'"""
                )
            else:
                cur.execute(
                    f"""SELECT DISTINCT subject FROM statements
                    WHERE predicate = 'rdf:type' AND object = 'owl:Class'
                    AND subject NOT LIKE '_:%'"""
                )
        else:
            cur.execute(
                """SELECT DISTINCT subject FROM statements
                WHERE predicate = 'rdf:type'
                AND object IN ('owl:ObjectProperty',
                               'owl:DataProperty',
                               'owl:AnnotationProperty')"""
            )
    term_ids = []
    for row in cur.fetchall():
        term_ids.append(row[0])
    return term_ids


def get_tree(term_id):
    db = get_database("ontie")
    fmt = request.args.get("format", "")
    if fmt == "json":
        label = request.args.get("text", "")
        return gizmos.search.search(db, label, limit=30)
    href = "./{curie}"
    if not term_id:
        href = "ontology/{curie}"
    content = gizmos.tree.tree(db, term_id, title="ONTIE Browser", href=href, include_search=True)
    with open("templates/tree.html.jinja2", "r") as f:
        template = Template(f.read())
    return template.render(content=content)
