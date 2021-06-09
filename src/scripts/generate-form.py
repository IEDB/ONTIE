import csv

from argparse import ArgumentParser
from jinja2 import Template


def build_form_field(input_type, column, help_msg, required, value=None):
    """Return an HTML form field for a template field."""
    if required:
        display = column + " *"
    else:
        display = column

    html = [
        '<div class="row mb-3">',
        f'\t<label class="col-sm-2 col-form-label">{display}</label>',
        '\t<div class="col-sm-10">',
    ]

    field_name = column.replace(" ", "-")

    value_html = ""
    if value:
        value_html = f' value="{value}"'
    if not value:
        value = ""

    if input_type == "text":
        if required:
            html.append(
                f'\t\t<input type="text" class="form-control" name="{field_name}" required{value_html}>'
            )
            html.append('\t\t<div class="invalid-feedback">')
            html.append(f"\t\t\t{column} is required")
            html.append("</div>")
        else:
            html.append(
                f'\t\t<input type="text" class="form-control" name="{field_name}"{value_html}>'
            )

    elif input_type == "textarea":
        if required:
            html.append(
                f'\t\t<textarea class="form-control" name="{field_name}" rows="3" required>{value}</textarea>'
            )
            html.append('\t\t<div class="invalid-feedback">')
            html.append(f"\t\t\t{column} is required")
            html.append("</div>")
        else:
            html.append(
                f'\t\t<textarea class="form-control" name="{field_name}" rows="3">{value}</textarea>'
            )

    elif input_type == "search":
        if required:
            html.append(
                f'<input type="text" class="search form-control" name="{field_name}" '
                + f'id="{field_name}-typeahead-obi" required{value_html}>'
            )
            html.append('\t\t<div class="invalid-feedback">')
            html.append(f"\t\t\t{column} is required")
            html.append("</div>")
        else:
            html.append(
                f'<input type="text" class="typeahead form-control" name="{field_name}" '
                + f'id="{field_name}-typeahead-obi"{value_html}>'
            )

    elif input_type.startswith("select"):
        selects = input_type.split("(", 1)[1].rstrip(")").split(", ")
        html.append(f'\t\t<select class="form-select" name="{field_name}">')
        for s in selects:
            if s == value:
                html.append(f'\t\t\t<option value="{s}" selected>{s}</option>')
            else:
                html.append(f'\t\t\t<option value="{s}">{s}</option>')
        html.append("\t\t</select>")

    else:
        return None

    if help_msg:
        html.append(f'\t\t<div class="form-text">{help_msg}</div>')
    html.append("\t</div>")
    html.append("</div>")
    return html


def build_form_html(fields, values=None, hidden=None):
    html = []
    if hidden:
        for name, value in hidden.items():
            html.append(f'<input type="hidden" name="{name}" value="{value}">')
    for field, details in fields.items():
        input_type = details.get("type")
        value = None
        if values:
            value = values[field]
        form_field = build_form_field(
            input_type, field, details.get("help"), details.get("required"), value=value
        )
        if not form_field:
            abort(500, f"Unknown input type '{input_type}' for column '{field}'")
        html.extend(form_field)
    return html


def build_message(message_content):
    """Return a pop-up message to display at the top of the page."""
    message_type = "success"
    if message_content.startswith("Unable"):
        message_type = "danger"
    message = f'<div class="alert alert-{message_type} alert-dismissible fade show" role="alert">\n'
    message += f'<p class="mb-0">{message_content}</p>\n'
    message += '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>\n'
    message += "</div>\n"
    return message


def get_template_fields(template):
    metadata_fields = {"ID": {"type": "text", "required": "true"}}
    logic_fields = {}
    with open(f"src/ontology/templates/{template}.tsv", "r") as f:
        reader = csv.DictReader(f, delimiter="\t")
        template_strings = next(reader)
        for header, template in template_strings.items():
            if template == "LABEL":
                metadata_fields[header] = {"type": "text", "required": "true"}
            elif template == "A definition":
                metadata_fields[header] = {"type": "textarea", "required": "true"}
            elif template.startswith("A"):
                metadata_fields[header] = {"type": "text"}
            elif template.strip() == "":
                metadata_fields[header] = {"type": "text"}
            else:
                logic_fields[header] = {"type": "search"}
    return metadata_fields, logic_fields


def main():
    parser = ArgumentParser()
    parser.add_argument("template")
    parser.add_argument("branch")
    parser.add_argument("message")
    args = parser.parse_args()


    metadata_fields, logic_fields = get_template_fields(args.template)
    metadata_html = "\n".join(build_form_html(metadata_fields))
    logic_html = "\n".join(build_form_html(logic_fields))
    with open("src/scripts/form.html", "r") as f:
        t = Template(f.read())
        message = ""
        if args.message != "None":
            message = build_message(args.message)
        html = t.render(title=args.template, message=message, branch=args.branch, metadata=metadata_html, logic=logic_html)
        print(html)


if __name__ == '__main__':
    main()
