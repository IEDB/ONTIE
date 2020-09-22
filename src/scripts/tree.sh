#!/usr/bin/env bash
#
# This simple CGI script helps create a new Google Sheet
# and share it with the user.

cd ../..

URL="http://example.com?${QUERY_STRING}"
ID=$(urlp --query --query_field=id "${URL}")

if [[ ${ID} ]]; then
	python3 -m gizmos.tree build/ontie.db ${ID}
else
	python3 -m gizmos.tree build/ontie.db owl:Thing
fi
