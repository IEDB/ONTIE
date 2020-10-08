import lxml.html.soupparser
import lxml.html
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
            html = f.read()
            root = lxml.html.soupparser.fromstring(html)

            contents = []
            for elem in root.xpath("//div[@class='highlighter']"):
                contents.append(lxml.html.tostring(elem, pretty_print=True).decode("utf-8"))
            pages.append({"name": n, "contents": "\n".join(contents)})

    first = pages.pop(0)

    # sys.stdout.write("Content-Type: text/html\n\n")
    sys.stdout.write(template.render(first=first, pages=pages))


if __name__ == '__main__':
    main()
