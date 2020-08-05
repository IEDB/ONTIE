import csv
import re
import sys

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
    problem_id = 1

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
        # Start at row idx 3; row 1 is headers, row 2 is template strings
        row_idx = 3
        for row in reader:
            curie = row["ID"]
            label = row["Label"]
            if not label or label.strip() == "":
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/missing_label",
                        "rule name": "missing label",
                        "value": "",
                        "fix": "add a label",
                    }
                )
                problem_id += 1
                continue

            # Check for label whitespace
            if label.strip() != label:
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/label_whitespace",
                        "rule name": "label whitespace",
                        "value": label,
                        "fix": "remove leading or trailing whitespace",
                    }
                )
                problem_id += 1

            # Check for label formatting
            if "\n" in label or "\t" in label:
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/label_formatting",
                        "rule name": "label formatting",
                        "value": label,
                        "fix": "remove any newline or tab characters from label",
                    }
                )
                problem_id += 1

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
                            "ID": problem_id,
                            "table": args.index,
                            "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                            "level": "warn",
                            "rule ID": "ROBOT:report_queries/missing_obsolete_label",
                            "rule name": "missing obsolete label",
                            "value": label,
                            "fix": "add 'obsolete' to beginning of label",
                        }
                    )
                    problem_id += 1
            elif label.startswith("obsolete"):
                # not obsolete = true, but label begins with 'obsolete'
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/misused_obsolete_label",
                        "rule name": "misused obsolete label",
                        "value": label,
                        "fix": "remove 'obsolete' from label OR annotate with obsolete = true",
                    }
                )
                problem_id += 1
            row_idx += 1

    # Check for multiple labels
    for curie, labels in curie_to_labels.items():
        if len(labels) > 1:
            all_locs = labels.keys()
            for loc, label in labels.items():
                other_locs = ", ".join([x for x in all_locs if x != loc])
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/multiple_labels",
                        "rule name": "multiple labels",
                        "value": label,
                        "fix": f"select one label from this cell & {other_locs}",
                    }
                )
                problem_id += 1

    # Check for duplicate labels
    for label, curies in label_to_curies.items():
        if len(curies) > 1:
            all_locs = curies.keys()
            for loc, curie in curies.items():
                other_locs = ", ".join([x for x in all_locs if x != loc])
                problems.append(
                    {
                        "ID": problem_id,
                        "table": args.index,
                        "cell": idx_to_a1(row_idx, headers.index("Label") + 1),
                        "level": "error",
                        "rule ID": "ROBOT:report_queries/duplicate_label",
                        "rule name": "duplicate label",
                        "value": label,
                        "fix": f"rename this term or term(s) at {other_locs}",
                    }
                )
                problem_id += 1

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
                    if not value or value.strip() == "":
                        continue
                    if value.strip() != value:
                        problems.append(
                            {
                                "ID": problem_id,
                                "table": template,
                                "cell": idx_to_a1(row_idx, headers.index(h) + 1),
                                "level": "warn",
                                "rule ID": "ROBOT:report_queries/annotation_whitespace",
                                "rule name": "annotation whitespace",
                                "value": value,
                                "fix": "remove leading or trailing whitespace",
                            }
                        )
                        problem_id += 1

                if "Parent" in headers:
                    if not row["Parent"] or row["Parent"].strip() == "":
                        # No superclass
                        problems.append(
                            {
                                "ID": problem_id,
                                "table": template,
                                "cell": idx_to_a1(row_idx, headers.index("Parent") + 1),
                                "level": "info",
                                "rule ID": "ROBOT:report_queries/missing_superclass",
                                "rule name": "missing superclass",
                                "value": "",
                                "fix": "maybe add a parent, or ignore if valid",
                            }
                        )
                        problem_id += 1

                if "Definition" in headers:
                    definition = row["Definition"]
                    if not definition or definition.strip() == "":
                        # No definition
                        problems.append(
                            {
                                "ID": problem_id,
                                "table": template,
                                "cell": idx_to_a1(
                                    row_idx, headers.index("Definition") + 1
                                ),
                                "level": "warn",
                                "rule ID": "ROBOT:report_queries/missing_definition",
                                "rule name": "missing definition",
                                "value": "",
                                "fix": "add a definition",
                            }
                        )
                        problem_id += 1
                    else:
                        loc = idx_to_a1(row_idx, headers.index("Definition") + 1)
                        if not re.match(r"^[A-Z]", definition.strip()):
                            problems.append(
                                {
                                    "ID": problem_id,
                                    "table": template,
                                    "cell": loc,
                                    "level": "info",
                                    "rule ID": "ROBOT:report_queries/lowercase_definition",
                                    "rule name": "lowercase definition",
                                    "value": definition,
                                    "fix": "capitalize the first letter, or ignore",
                                }
                            )
                            problem_id += 1

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
                    alt_terms = row["Alternative Term"]
                    if not alt_terms or alt_terms.strip() == "":
                        continue
                    alt_terms = alt_terms.split("|")
                    for at in alt_terms:
                        loc = idx_to_a1(row_idx, headers.index("Alternative Term") + 1)
                        at = at.strip()
                        if at in alt_term_to_locs:
                            locs = alt_term_to_locs[at]
                        else:
                            locs = []
                        locs.append(loc)
                        alt_term_to_locs[at] = locs

                row_idx += 1

        # Check for multiple definitions
        for curie, definitions in curie_to_definitions.items():
            if len(definitions) > 1:
                all_locs = definitions.keys()
                for loc, definition in definitions.items():
                    other_locs = ", ".join([x for x in all_locs if x != loc])
                    problems.append(
                        {
                            "ID": problem_id,
                            "table": template,
                            "cell": loc,
                            "level": "error",
                            "rule ID": "ROBOT:report_queries/multiple_definitions",
                            "rule name": "multiple definitions",
                            "value": definition,
                            "fix": f"select one definition from this cell & {other_locs}",
                        }
                    )
                    problem_id += 1

        # Check for duplicate definitions
        for definition, locs in definition_to_locs.items():
            if len(locs) > 1:
                for loc in locs:
                    other_locs = ", ".join([x for x in locs if x != loc])
                    problems.append(
                        {
                            "ID": problem_id,
                            "table": template,
                            "cell": loc,
                            "level": "error",
                            "rule ID": "ROBOT:report_queries/duplicate_definition",
                            "rule name": "duplicate definitions",
                            "value": definition,
                            "fix": f"rewrite this definition or the definition(s) at {other_locs}",
                        }
                    )
                    problem_id += 1

        # Check for duplicate alt terms (exact synonyms)
        for alt_term, locs in alt_term_to_locs.items():
            if len(locs) > 1:
                for loc in locs:
                    other_locs = ", ".join([x for x in locs if x != loc])
                    problems.append(
                        {
                            "ID": problem_id,
                            "table": template,
                            "cell": loc,
                            "level": "warn",
                            "rule ID": "ROBOT:report_queries/duplicate_exact_synonym",
                            "rule name": f"duplicate exact synonym '{alt_term}'",
                            "value": alt_term,
                            "fix": f"assign unique synonyms to this cell & {other_locs}",
                        }
                    )
                    problem_id += 1

    # Write problems table to stdout
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=[
            "ID",
            "table",
            "cell",
            "level",
            "rule ID",
            "rule name",
            "value",
            "fix",
        ],
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(problems)


if __name__ == "__main__":
    main()
