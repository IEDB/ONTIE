#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ../..

URL="http://example.com?${QUERY_STRING}"
TEMPLATE=$(urlp --query --query_field=template "${URL}")
ADD=$(urlp --query --query_field=add "${URL}")
BRANCH=$(git branch --show-current)

MESSAGE="None"
if [[ ${ADD} ]]; then
	QS=$(urlp --query "${URL}")
	MESSAGE=$(python3 src/scripts/add-term.py "${QS}")
fi

echo "Content-Type: text/html"
echo ""
python3 src/scripts/generate-form.py ${TEMPLATE} ${BRANCH} "${MESSAGE}"
