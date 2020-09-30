#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ../..

URL="http://example.com?${QUERY_STRING}"
ID=$(urlp --query --query_field=id "${URL}")
DB=$(urlp --query --query_field=db "${URL}")
BRANCH=$(git branch --show-current)

if [[ ${DB} ]]; then
	if [[ ${ID} ]]; then
		python3 -m gizmos.tree resources/${DB}.db ${ID} -i
	else
		python3 -m gizmos.tree resources/${DB}.db -i
	fi
	echo "<a href=\"./tree.sh\"><b>Select a new tree</b></a><br>"
	echo "<a href=\"/ONTIE/branches/${BRANCH}\"><b>Return Home</b></a>"
else
	echo "Content-Type: text/html"
	echo ""
	echo "<h3>Select a tree:</h3>"
	echo "<ul>"
	echo "<li><a href=\"?db=ontie\">IEDB Source of Truth (ONTIE)</a></li>"
	echo "<li><b>Imports:</b></li>"
	echo "<ul>"
	echo "<li><a href=\"?db=doid&id=DOID:4\">Human Disease Ontology (DOID)</a></li>"
	echo "<li><a href=\"?db=obi\">Ontology for Biomedical Investigations (OBI)</a></li>"
	echo "</ul>"
	echo "</ul>"
	echo "<a href=\"/ONTIE/branches/${BRANCH}\"><b>Return Home</b></a>"
fi
