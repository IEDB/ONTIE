import csv
import sys

from argparse import ArgumentParser
from urllib.parse import parse_qs


DEFAULTS = ["add", "branch", "branch-name", "project-name", "view-path"]


def main():
	parser = ArgumentParser()
	parser.add_argument("query_string")
	args = parser.parse_args()

	fields = parse_qs(args.query_string)
	for default in DEFAULTS:
		if default in fields:
			del fields[default]

	fields = {k: v[0] for k, v in fields.items()}

	template = None
	if "template" in fields:
		template = fields["template"]
		del fields["template"]
	term_id = None
	if "ID" in fields:
		term_id = fields["ID"]
		del fields["ID"]

	if not template:
		print("Unable to add term; missing template name")
		sys.exit(1)
	if not term_id:
		print("Unable to add term; an ID is required")
		sys.exit(1)
	if not fields.get("Label"):
		print("Unable to add term; a Label is required")
		sys.exit(1)

	template_path = f"src/ontology/templates/{template}.tsv"

	rows = []
	with open("src/ontology/templates/index.tsv", "r") as fr:
		reader = csv.DictReader(fr, delimiter="\t")
		header = reader.fieldnames
		for row in reader:
			this_id = row["ID"]
			if this_id == term_id:
				this_label = row["Label"]
				print(f"Unable to add term; a term already exists with ID {term_id} ({this_label})")
				sys.exit(1)
			rows.append(row)
	rows.append({"ID": term_id, "Label": fields.get("Label"), "Type": "owl:Class"})

	with open("src/ontology/templates/index.tsv", "w") as fw:
		writer = csv.DictWriter(fw, delimiter="\t", fieldnames=header, lineterminator="\n", extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)

	rows = []
	with open(template_path, "r") as fr:
		reader = csv.DictReader(fr, delimiter="\t")
		header = reader.fieldnames
		for row in reader:
			rows.append(row)
	rows.append(fields)

	with open(template_path, "w") as fw:
		writer = csv.DictWriter(fw, delimiter="\t", fieldnames=header, lineterminator="\n", extrasaction="ignore")
		writer.writeheader()
		writer.writerows(rows)

	print(f"{term_id} successfully added to ONITE!")


if __name__ == '__main__':
	main()

