import logging
import re
import sys

from argparse import ArgumentParser
from jinja2 import Template


def main():
    p = ArgumentParser()
    p.add_argument("template")
    p.add_argument("names", nargs="+")
    args = p.parse_args()

    with open(args.template, "r") as f:
        template = Template(f.read())

    pages = []
    for n in args.names:
        with open(f"build/diff/{n}.html", "r") as f:
            html_search = re.search(r"<body>(.+)<\/body>", f.read(), re.DOTALL)
            if html_search:
                contents = html_search.group(1)
            else:
                logging.error("Unable to extract contents from " + n)
                continue
            pages.append({"name": n, "contents": contents})

    first = pages.pop(0)

    # sys.stdout.write("Content-Type: text/html\n\n")
    sys.stdout.write(template.render(first=first, pages=pages))


if __name__ == '__main__':
    main()
