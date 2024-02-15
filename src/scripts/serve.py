#!/usr/bin/env python3

# Serve HCC-KB development and curation site,
# calling Nanobot to do the hard work.

import csv
import os
import subprocess

from bottle import get, post, request, response, run, static_file, HTTPError
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


@get('/')
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


@get('/documentation')
def documentation():
    with open('doc/api.md') as f:
        output = '<div class="container-lg">'
        output += markdown(f.read(), extensions=['fenced_code', 'codehilite'])
        output += '</div>'
        return render(output)


@get('/file/<filename>')
def get_file(filename):
    return static_file(filename, root='build/download/')


@get('/<resource>')
def get_resource(resource):
    return nanobot('GET', resource, '')


@get('/<resource>/<path:path>')
def get_resource_path(resource, path):
    return nanobot('GET', resource, path)


def nanobot(method, resource, path):
    """Call Nanobot as a CGI script
    for the given resource, and path."""
    if method not in ['GET', 'POST']:
        raise HTTPError(f'Bad method {method}')
    resource = resource.replace('-','_')
    path_info = resource
    if path:
        path_info = '/'.join([resource, path])

    result = subprocess.run(
        [os.path.join(os.getcwd(), 'bin/nanobot')],
        env={
            'GATEWAY_INTERFACE': 'CGI/1.1',
            'REQUEST_METHOD': method,
            'PATH_INFO': path_info,
            'QUERY_STRING': request.query_string,
        },
        input=request.body.getvalue().decode('utf-8'),
        text=True,
        capture_output=True
    )
    reading_headers = True
    body = []
    for line in result.stdout.splitlines():
        if reading_headers and line.strip() == '':
            reading_headers = False
            continue
        if reading_headers:
            name, value = line.split(': ', 1)
            if name == 'status':
                response.status = value
            else:
                response.set_header(name, value)
        else:
            body.append(line)
    return '\n'.join(body)


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


run(host='0.0.0.0', port=3000)
