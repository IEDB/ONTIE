# #TAXDMP_VERSION := $(shell date +"%Y-%m-01")
# TAXDMP_VERSION := 2026-08-01

# # Fetch the taxdmp.zip for this month.
# cache/ncbitaxon/taxdmp_$(TAXDMP_VERSION).zip: | cache/ncbitaxon/ current/
# 	curl -L -o $@ https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump_archive/taxdmp_$(TAXDMP_VERSION).zip

import csv


def update():
    delnodes = set()
    with open('delnodes.dmp') as f:
        for line in f.readlines():
            parts = line.split('|')
            tax_id = int(parts[0].strip())
            delnodes.add(tax_id)

    merged = {}
    with open('merged.dmp') as f:
        for line in f.readlines():
            parts = line.split('|')
            old_tax_id = int(parts[0].strip())
            new_tax_id = int(parts[1].strip())
            merged[old_tax_id] = new_tax_id

    scientific_names = {}
    with open('names.dmp') as f:
        for line in f.readlines():
            parts = line.split('|')
            tax_id = int(parts[0].strip())
            name_type = parts[3].strip()
            if name_type == 'scientific name':
                name = parts[1].strip()
                unique = parts[2].strip()
                scientific_names[tax_id] = unique or name 

    # nodes = {}
    # with open('nodes.dmp') as f:
    #     for line in f.readlines():
    #         parts = line.split('|')
    #         tax_id = int(parts[0].strip())
    #         nodes[tax_id] = [part.strip() for part in parts[1:]]

    renamed = {}

    # Replace merged NCBI Taxa with their replacements,
    # and update labels.
    with open('src/ontology/templates/external.tsv') as f:
        external_rows = list(csv.DictReader(f, delimiter='\t'))
    for row in external_rows:
        curie = row['ID']
        if not curie.startswith('NCBITaxon:'):
            continue
        tax_id = curie.replace('NCBITaxon:', '')
        try:
            tax_id = int(tax_id)
        except Exception:
            continue

        if tax_id in delnodes:
            print(f'WARN: deleted node {tax_id}')
        if tax_id in merged:
            tax_id = merged[tax_id]
            if tax_id in merged:
                print(f'WARN: merged TWICE node {tax_id}')
            row['ID'] = f'NCBITaxon:{tax_id}'

        old_name = row['Label']
        if old_name in renamed:
            print(f'WARN: already replaced {old_name}')
        new_name = scientific_names[tax_id]
        if old_name != new_name:
            renamed[old_name] = new_name
            row['Label'] = new_name

    renamed_ncbi_taxa = len(renamed)
    print('Renemd NCBI Taxa:', renamed_ncbi_taxa)

    # Check external_rows for duplicates.
    curies = set()
    labels = set()
    for row in external_rows:
        curie = row['ID']
        if curie in curies:
            print(f'WARN: duplicate CURIE in external {curie}')
        curies.add(curie)
        label = row['Label']
        if label in labels:
            print(f'WARN: duplicate label in external {label}')
        labels.add(label)
    curies.remove('owl:Thing')
    labels.remove('owl:Thing')
    
    # Write external rows.
    robot_header = external_rows.pop(0)
    fieldnames = list(robot_header.keys())
    rows = sorted(external_rows, key=lambda x: x['ID'])
    with open('src/ontology/templates/external.tsv', 'w') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerow(robot_header)
        writer.writerows(rows)

    # Check organism table for renamed IEDB taxa.
    organisms = {}
    with open('organism.tsv') as f:
        rows = csv.DictReader(f, delimiter='\t')
        for row in rows:
            iri = row['iri']
            if not iri:
                continue
            curie = iri.replace('https://ontology.iedb.org/ontology/ONTIE_', 'ONTIE:')
            organisms[curie] = row

    # Rename IEDB taxa in index.
    with open('src/ontology/templates/index.tsv') as f:
        rows = list(csv.DictReader(f, delimiter='\t'))
    robot_header = rows.pop(0)
    for row in rows:
        curie = row['ID']
        if curie in curies:
            print(f'WARN: duplicate CURIE in index {curie}')
        curies.add(curie)
        if curie in organisms:
            old_label = row['Label']
            new_label = organisms[curie]['organism_name']
            if old_label != new_label:
                row['Label'] = new_label
                renamed[old_label] = new_label
        label = row['Label']
        if label in labels:
            print(f'WARN: duplicate label in index {label}')
        labels.add(label)

    renamed_iedb_taxa = len(renamed) - renamed_ncbi_taxa
    print('Renemd IEDB Taxa:', renamed_iedb_taxa)

    # Write updated index.
    path = 'src/ontology/templates/index.tsv'
    fieldnames = list(robot_header.keys())
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerow(robot_header)
        writer.writerows(rows)

    # Rename NCBI and IEDB taxa in these tables and columns.
    table_column = {
        'taxon': ['Label', 'Parent'],
        'protein': ['In Taxon'],
        'complex': ['In Taxon'],
    }

    for table, columns in table_column.items():
        path = f'src/ontology/templates/{table}.tsv'
        with open(path) as f:
            rows = list(csv.DictReader(f, delimiter='\t'))
        robot_header = rows.pop(0)
        for row in rows:
            for column in columns:
                old_terms = row[column].split('|')
                new_terms = []
                for old_term in old_terms:
                    new_term = renamed.get(old_term, old_term)
                    new_terms.append(new_term)
                for new_term in new_terms:
                    if new_term not in labels and new_term not in curies:
                        print(f'WARN: missing term from {table}.{column}: {new_term}')
                row[column] = '|'.join(new_terms)

        fieldnames = list(robot_header.keys())
        rows = sorted(rows, key=lambda x: x['Label'].lower())
        with open(path, 'w') as f:
            writer = csv.DictWriter(f, fieldnames, delimiter='\t', lineterminator='\n')
            writer.writeheader()
            writer.writerow(robot_header)
            writer.writerows(rows)


if __name__ == '__main__':
    update()
