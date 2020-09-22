#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ../..

URL="http://example.com?${QUERY_STRING}"
ID=$(urlp --query --query_field=id "${URL}")
ID="${ID:-owl:Thing}"

if [[ ${ID} ]]; then
	python3 -m gizmos.tree build/ontie.db ${ID}
else
	python3 -m gizmos.tree build/ontie.db owl:Thing
fi
