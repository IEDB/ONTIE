#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ../..

URL="http://example.com?${QUERY_STRING}"
ID=$(urlp --query --query_field=id "${URL}")
ID="${ID:-owl:Thing}"

python3 -m gizmos.tree build/ontie.db ${ID}
