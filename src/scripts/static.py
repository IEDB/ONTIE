#!/usr/bin/env python3

# Build static pages for ontology.iedb.org.

from jinja2 import Environment, FileSystemLoader
from markdown import markdown


resources = {
    "ontie": {
        "title": "ONTIE: Ontology for Immune Epitopes",
        "root": "owl:Class",
    },
    "disease-tree": {
        "title": "IEDB Disease Tree",
        "root": "ONTIE:0003543",
    }
}

env = Environment(
    loader=FileSystemLoader('src/templates/')
)


def index():
    output = [
        '<div class="container-lg pt-3">',
        '  <h2>IEDB Source of Terminology</h2>',
        '  <p>',
        '    Search and browse the ontologies that support the',
        '    <a href="https://www.iedb.org">Immune Epitope Database (IEDB)</a>.',
        '  </p>',
        '  <form class="form">',
        '    <input id="tree-typeahead-form" class="search typeahead w-100" type="input" placeholder="Search..." />',
        '  </form>',
        '  <p class="text-body-secondary pt-2">Examples:',
    ]

    examples = ['BALB/c', 'animal model of cancer', '17 kDa protein']
    output.append(', '.join(examples))

    output += [
        '  </p>',
        '  <table class="table">',
        '    <tr>',
        '      <th>Ontology</th>',
        '      <th><a href="https://www.w3.org/OWL/">OWL Ontology</a></th>',
        '      <th><a href="https://github.com/ontodev/ldtab">LDTab Table</a></th>',
        '    </tr>',
    ]
    for resource, value in resources.items():
        output += [
            '    <tr>',
            f'      <td><a href="{resource}/{value["root"]}">{value["title"]}</a></td>',
            f'      <td><a href="file/{resource}.owl">{resource}.owl</a></td>',
            f'      <td><a href="file/{resource}.tsv">{resource}.tsv</a></td>',
            '    </tr>',
        ]
    output += [
        '  </table>',
        '  <h3>Other Resources</h3>',
        '  <ul>',
        '    <li><a href="/prefix">Table of prefixes</a></li>',
        '    <li><a href="https://github.com/IEDB/ONTIE">ONTIE GitHub Repsitory</a></li>',
        '    <li><a href="https://help.iedb.org/hc/en-us/articles/4402872882189-Immune-Epitope-Database-Query-API-IQ-API">Immune Epitope Database Query API (IQ-API)</a></li>',
        '  </ul>',
        '</div>'
    ]
    return render('\n'.join(output))


def documentation():
    with open('doc/api.md') as f:
        output = '<div class="container-lg">'
        output += markdown(f.read(), extensions=['fenced_code', 'codehilite'])
        output += '</div>'
        return render(output)


def render(content):
    """Given an HTML content string,
    render the `page.html` template
    and return the resulting HTML string."""
    template = env.from_string('''{% extends "page.html" %}
{% block content %}
    {{ content }}
{% endblock %}''')
    return template.render(
        page={
            'project_name': 'IEDB Terminology',
            'tables': {
            },
        },
        table_name='ontology',
        tree='ontology',
        content=content
    )


if __name__ == "__main__":
    with open("site/index.html", "w") as f:
        f.write(index())
    with open("site/documentation.html", "w") as f:
        f.write(documentation())
