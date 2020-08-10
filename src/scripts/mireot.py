import sqlite3

from argparse import ArgumentParser

# Track terms already added to database
added = []


def add_term(cur, term_id):
    """Add the class assertion for a term ID, assuming that term ID exists in the database."""
    cur.execute(f"SELECT * FROM statements WHERE subject = '{term_id}';")
    res = cur.fetchone()
    if res:
        cur.execute(
            f"""INSERT INTO extract (stanza, subject, predicate, object)
                        VALUES ('{term_id}', '{term_id}', 'rdf:type', 'owl:Class');"""
        )


def add_ancestors(cur, term_id):
    """Add the hierarchy for a term ID starting with that term up to the top-level, assuming that
    term ID exists in the database."""
    global added
    cur.execute(
        f"""
          WITH RECURSIVE ancestors(parent, child) AS (
            VALUES ('{term_id}', NULL)
            UNION
            SELECT object AS parent, subject AS child
            FROM statements
            WHERE predicate = 'rdfs:subClassOf'
              AND object = '{term_id}'
            UNION
            SELECT object AS parent, subject AS child
            FROM statements, ancestors
            WHERE ancestors.parent = statements.stanza
              AND statements.predicate = 'rdfs:subClassOf'
              AND statements.object NOT LIKE '_:%'
          )
          SELECT * FROM ancestors;"""
    )

    for row in cur.fetchall():
        parent = row["parent"]
        if parent and parent not in added:
            # Only add rdf:type if it hasn't been added
            added.append(parent)
            cur.execute(
                f"""INSERT INTO extract (stanza, subject, predicate, object)
                            VALUES ('{parent}', '{parent}', 'rdf:type', 'owl:Class');"""
            )

        child = row["child"]
        if child and child not in added:
            # Only add rdf:type if it hasn't been added
            added.append(child)
            cur.execute(
                f"""INSERT INTO extract (stanza, subject, predicate, object)
                            VALUES ('{child}', '{child}', 'rdf:type', 'owl:Class');"""
            )

        if child and parent:
            # Row has child & parent, add subclass statement
            cur.execute(
                f"""INSERT INTO extract (stanza, subject, predicate, object)
                            VALUES ('{child}', '{child}', 'rdfs:subClassOf', '{parent}');"""
            )


def dict_factory(cursor, row):
    """Create a dict factory for sqlite cursor"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def main():
    global added
    p = ArgumentParser()
    p.add_argument("-d", "--database", required=True, help="SQLite database")
    p.add_argument(
        "-t",
        "--terms",
        required=True,
        help="File containing CURIES of terms to extract",
    )
    p.add_argument(
        "-a",
        "--annotation",
        action="append",
        help="CURIE of annotation property to include",
    )
    p.add_argument(
        "-A",
        "--annotations",
        help="File containing CURIEs of annotation properties to include",
    )
    p.add_argument(
        "-n",
        "--no_hierarchy",
        action="store_true",
        help="If provided, do not create any rdfs:subClassOf statements",
    )
    p.add_argument("-o", "--output", required=True, help="TTL output")
    args = p.parse_args()

    # Get required terms
    with open(args.terms, "r") as f:
        terms = f.readlines()
    terms = [x.strip() for x in terms]

    # Get optional annotations (otherwise, all annotations are included)
    annotations = None
    if args.annotation:
        # One or more annotations to add
        annotations = args.annotation
    if args.annotations:
        with open(args.annotations, "r") as f:
            annotations = f.readlines()
    if annotations:
        annotations = ["'" + x.strip().replace("'", "''") + "'" for x in annotations]
        annotations = ", ".join(annotations)

    # Create a new table (extract) and copy the triples we care about
    # Then write the triples from that table to the output file
    with sqlite3.connect(args.database) as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()

        # Create the extract table
        cur.execute("DROP TABLE IF EXISTS extract;")
        cur.execute(
            """CREATE TABLE extract(stanza TEXT,
                              subject TEXT,
                              predicate TEXT,
                              object TEXT,
                              value TEXT,
                              datatype TEXT,
                              language TEXT);"""
        )

        # Get each term up to the top-level (unless no_hierarchy)
        if not args.no_hierarchy:
            for t in terms:
                add_ancestors(cur, t)
        else:
            # Only add the terms themselves (as long as they exist)
            for t in terms:
                add_term(cur, t)

        # Add annotations for all subjects
        cur.execute("SELECT DISTINCT subject FROM extract;")
        for row in cur.fetchall():
            subject = row["subject"]
            query = f"""INSERT INTO extract (stanza, subject, predicate, value, language, datatype)
                        SELECT DISTINCT
                          subject AS stanza,
                          subject,
                          predicate,
                          value,
                          language,
                          datatype
                        FROM statements WHERE subject = '{subject}' AND value NOT NULL"""
            if annotations:
                query += f" AND predicate IN ({annotations})"
            cur.execute(query)

        # Reset row factory
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get ttl lines
        cur.execute(
            '''WITH literal(value, escaped) AS (
                      SELECT DISTINCT
                        value,
                        replace(replace(replace(value, '\\', '\\\\'), '"', '\\"'), '
                    ', '\\n') AS escaped
                      FROM extract
                    )
                    SELECT
                      "@prefix " || prefix || ": <" || base || "> ."
                    FROM prefix
                    UNION ALL
                    SELECT DISTINCT
                       subject
                    || " "
                    || predicate
                    || " "
                    || coalesce(
                         object,
                         """" || escaped || """^^" || datatype,
                         """" || escaped || """@" || language,
                         """" || escaped || """"
                       )
                    || " ."
                    FROM extract LEFT JOIN literal ON extract.value = literal.value;'''
        )
        lines = []
        for row in cur.fetchall():
            line = row[0]
            if not line:
                continue
            # Replace newlines
            line = line.replace("\n", "\\n")
            lines.append(line + "\n")

        # Write ttl
        with open(args.output, "w") as f:
            f.writelines(lines)


if __name__ == "__main__":
    main()
