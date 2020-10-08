#!/usr/bin/env bash
#
# This simple CGI script helps create a tree browser for ONTIE

cd ../..

URL="http://example.com?${QUERY_STRING}"
ID=$(urlp --query --query_field=id "${URL}")
DB=$(urlp --query --query_field=db "${URL}")
BRANCH=$(git branch --show-current)

if [[ ${DB} ]]; then
	# Check that the sqlite database exists
	if ! [[ -s build/${DB}.db ]]; then
		make build/${DB}.db > /dev/null 2>&1
	fi

	# Generate the tree view
	if [[ ${ID} ]]; then
		python3 -m gizmos.tree build/${DB}.db ${ID} -i
	else
		python3 -m gizmos.tree build/${DB}.db -i
	fi

	echo "<a href=\"./tree.sh\"><b>Select a new tree</b></a><br>"
	echo "<a href=\"/ONTIE/branches/${BRANCH}\"><b>Return Home</b></a>"
else
	echo "Content-Type: text/html"
	echo ""
	echo "<h3>Select a tree:</h3>"
	echo "<ul>"
	echo "<li><a href=\"?db=ontie\">Ontology for Immune Epitopes (ONTIE)</a></li>"
	echo "<li><b>Imports:</b></li>"
	echo "<ul>"
	echo "<li><a href=\"?db=doid&id=DOID:4\">Human Disease Ontology (DOID)</a></li>"
	echo "<li><a href=\"?db=obi\">Ontology for Biomedical Investigations (OBI)</a></li>"
	echo "</ul>"
	echo "</ul>"
	echo "<p>If you are selecting a tree for the first time, it may take some time to build the database!</p>"
	echo "<a href=\"/ONTIE/branches/${BRANCH}\"><b>Return Home</b></a>"
fi
