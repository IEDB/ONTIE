import csv
import re
import sys

import logging

from argparse import ArgumentParser


def idx_to_a1(row, col):
    """Convert a row & column to A1 notation. Adapted from gspread.utils."""
    div = col
    column_label = ""

    while div:
        (div, mod) = divmod(div, 26)
        if mod == 0:
            mod = 26
            div -= 1
        column_label = chr(mod + 64) + column_label

    label = f"{column_label}{row}"
    return label


def main():
    p = ArgumentParser()
    p.add_argument("-i", "--index", help="Path to index template")
    p.add_argument(
        "-t", "--templates", nargs="*", help="Paths to other templates to report on"
    )
    args = p.parse_args()

    # ID -> Label (loc -> value) to check for multiple labels
    curie_to_labels = {}

    # Label -> ID (loc -> ID) to check for duplicate labels
    label_to_curies = {}

    obsolete = []

    problems = []

    # Read in index to collect ID -> Label
    delim = "\t"
    if args.index.endswith("csv"):
        delim = ","
    with open(args.index, "r") as f:
        # ID, Label, Type, obsolete, replacement
        reader = csv.DictReader(f, delimiter=delim)
        # Use headers to get the column idx
        headers = reader.fieldnames
        # Skip template string row
        next(reader)
        # Start at row idx 3; 1=headers, 2=template, 3=validate
        row_idx = 3
        for row in reader:
            row_idx += 1
            curie = row["ID"]
            label = row["Label"]
            if not label or label.strip() == "":
                problems.append(
                    {
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/missing_label",
                        "rule": "missing label",
                        "message": "add a label",
                    }
                )
                continue

            # Check for label whitespace
            if label.strip() != label:
                problems.append(
                    {
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/label_whitespace",
                        "rule": "label whitespace",
                        "suggestion": label.strip(),
                        "message": "remove leading and trailing whitespace from label",
                    }
                )

            # Check for label formatting
            if "\n" in label or "\t" in label:
                problems.append(
                    {
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/label_formatting",
                        "rule": "label formatting",
                        "suggestion": label.replace("\n", " ").replace("\t", " "),
                        "message": "remove new lines and tabs from label",
                    }
                )

            # Add to CURIE -> Label map
            if curie in curie_to_labels:
                labels = curie_to_labels[curie]
            else:
                labels = {}
            labels[idx_to_a1(row_idx, headers.index("Label") + 1)] = label
            curie_to_labels[curie] = labels

            # Add to Label -> CURIE map
            if label in label_to_curies:
                curies = label_to_curies[label]
            else:
                curies = {}
            curies[idx_to_a1(row_idx, headers.index("Label") + 1)] = curie
            label_to_curies[label] = curies

            # Obsolete checks
            if row["obsolete"].lower() == "true":
                obsolete.append(curie)
                # Check for missing obsolete labels
                if not label.lower().startswith("obsolete"):
                    problems.append(
                        {
                            "table": args.index,
                            "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                            "level": "warn",
                            "rule ID": "ROBOT:report_queries/missing_obsolete_label",
                            "rule": "missing obsolete label",
                            "suggestion": f"obsolete {label}",
                            "message": "add obsolete to beginning of label",
                        }
                    )
            elif label.startswith("obsolete"):
                # not obsolete = true, but label begins with 'obsolete'
                problems.append(
                    {
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/misused_obsolete_label",
                        "rule": "misused obsolete label",
                        "suggestion": label.split(" ", 1)[1],
                        "message": "remove obsolete from label or mark term as obsolete",
                    }
                )

    # Check for multiple labels
    for curie, labels in curie_to_labels.items():
        if len(labels) > 1:
            all_locs = labels.keys()
            for loc, label in labels.items():
                other_locs = ", ".join([x for x in all_locs if x != loc])
                problems.append(
                    {
                        "table": args.index,
                        "cell": loc,
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/multiple_labels",
                        "rule": "multiple labels",
                        "message": f"select one label from this & {other_locs}",
                    }
                )

    # Check for duplicate labels
    for label, curies in label_to_curies.items():
        if len(curies) > 1:
            all_locs = curies.keys()
            for loc, curie in curies.items():
                other_locs = ", ".join([x for x in all_locs if x != loc])
                problems.append(
                    {
                        "table": args.index,
                        "cell": loc,
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/duplicate_label",
                        "rule": "duplicate label",
                        "suggestion": f"",
                        "message": f"assign unique labels to this * {other_locs}",
                    }
                )

    # Make a map of Label -> CURIE for non-duplicate labels
    label_to_curie = {}
    for label, curies in label_to_curies.items():
        if len(curies) == 1:
            label_to_curie[label] = list(curies.keys())[0]

    for template in args.templates:
        # ID -> definition (loc -> value) for multiple definitions
        curie_to_definitions = {}

        # definition -> loc for duplicate definitions
        definition_to_locs = {}

        # alt term -> loc for duplicate alt terms
        alt_term_to_locs = {}

        delim = "\t"
        if template.endswith("csv"):
            delim = ","
        with open(template, "r") as f:
            # Required: Label, Parent
            # Optional: Definition, Alternative Term
            reader = csv.DictReader(f, delimiter=delim)
            headers = reader.fieldnames

            # Skip template string row
            next(reader)
            row_idx = 3

            for row in reader:
                row_idx += 1
                label = row["Label"]
                if label not in label_to_curie:
                    continue
                curie = label_to_curie[label]

                if curie in obsolete:
                    # Ignore obsolete terms
                    continue

                # Generic checks
                for h, value in row.items():
                    if not h:
                        break
                    # Check for whitespace
                    if value and value.strip() != "":
                        if value.strip() != value:
                            problems.append(
                                {
                                    "table": template,
                                    "cell": idx_to_a1(row_idx, headers.index(h) + 1),
                                    "level": "warn",
                                    "rule ID": "ROBOT:report_queries/annotation_whitespace",
                                    "rule": "annotation whitespace",
                                    "suggestion": value.strip(),
                                    "message": "remove leading and trailing whitespace",
                                }
                            )

                if "Parent" in headers:
                    if not row["Parent"] or row["Parent"].strip() == "":
                        # No superclass
                        problems.append(
                            {
                                "table": template,
                                "cell": idx_to_a1(row_idx, headers.index("Parent") + 1),
                                "level": "info",
                                "rule ID": "ROBOT:report_queries/missing_superclass",
                                "rule": "missing superclass",
                                "message": "add a superclass or ignore this message",
                            }
                        )

                if "Definition" in headers:
                    definition = row["Definition"]
                    loc = idx_to_a1(row_idx, headers.index("Definition") + 1)
                    if not definition or definition.strip() == "":
                        # No definition
                        problems.append(
                            {
                                "table": template,
                                "cell": loc,
                                "level": "warn",
                                "rule ID": "ROBOT:report_queries/missing_definition",
                                "rule": "missing definition",
                                "message": "add a definition",
                            }
                        )
                    else:
                        if not re.match(r"^[A-Z]", definition.strip()):
                            problems.append(
                                {
                                    "table": template,
                                    "cell": loc,
                                    "level": "info",
                                    "rule ID": "ROBOT:report_queries/lowercase_definition",
                                    "rule": "lowercase definition",
                                    "suggestion": definition.capitalize(),
                                    "message": "capitalize the first letter of the definition",
                                }
                            )

                        # Add ID -> def dict
                        if curie in curie_to_definitions:
                            defs = curie_to_definitions[curie]
                        else:
                            defs = {}
                        defs[loc] = definition
                        curie_to_definitions[curie] = defs

                        # Add to def -> ID dict
                        if definition in definition_to_locs:
                            locs = definition_to_locs[definition]
                        else:
                            locs = []
                        locs.append(loc)
                        definition_to_locs[definition] = locs

                if "Alternative Term" in headers:
                    loc = idx_to_a1(row_idx, headers.index("Alternative Term") + 1)
                    alt_terms = row["Alternative Term"]
                    if alt_terms and alt_terms.strip() != "":
                        alt_terms = alt_terms.split("|")
                        for at in alt_terms:
                            if at.strip != "":
                                at = at.strip()
                                if at in alt_term_to_locs:
                                    locs = alt_term_to_locs[at]
                                else:
                                    locs = []
                                locs.append(loc)
                                alt_term_to_locs[at] = locs

        # Check for multiple definitions
        for curie, definitions in curie_to_definitions.items():
            if len(definitions) > 1:
                all_locs = definitions.keys()
                for loc, definition in definitions.items():
                    other_locs = ", ".join([x for x in all_locs if x != loc])
                    problems.append(
                        {
                            "table": template,
                            "cell": loc,
                            "level": "error",
                            "rule ID": "ROBOT:report_queries/multiple_definitions",
                            "rule": "multiple definitions",
                            "message": f"select one definition from this & {other_locs}",
                        }
                    )

        # Check for duplicate definitions
        for definition, locs in definition_to_locs.items():
            if len(locs) > 1:
                for loc in locs:
                    other_locs = ", ".join([x for x in locs if x != loc])
                    problems.append(
                        {
                            "table": template,
                            "cell": loc,
                            "level": "error",
                            "rule ID": "ROBOT:report_queries/duplicate_definition",
                            "rule": "duplicate definitions",
                            "message": f"write unique definitions for this & {other_locs}",
                        }
                    )

        # Check for duplicate alt terms (exact synonyms)
        for alt_term, locs in alt_term_to_locs.items():
            if len(locs) > 1:
                for loc in locs:
                    other_locs = ", ".join([x for x in locs if x != loc])
                    problems.append(
                        {
                            "table": template,
                            "cell": loc,
                            "level": "warn",
                            "rule ID": "ROBOT:report_queries/duplicate_exact_synonym",
                            "rule": f"duplicate exact synonym '{alt_term}'",
                            "message": f"assign unique synonyms to this & {other_locs}",
                        }
                    )

    # Write problems table to stdout
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "table",
            "cell",
            "level",
            "rule ID",
            "rule",
            "message",
            "suggestion",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(problems)


if __name__ == "__main__":
    main()
