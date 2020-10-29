#!/usr/bin/env bash
#
# This simple CGI script helps create a new Google Sheet
# and share it with the user.

echo "Content-Type: text/html"
echo ""

cd ../..

EMAIL_PAT="^[a-z0-9!#\$%&'*+/=?^_\`{|}~-]+(\.[a-z0-9!#$%&'*+/=?^_\`{|}~-]+)*@([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]*[a-z0-9])?\$"
URL="http://example.com?${QUERY_STRING}" 
EMAIL=$(urlp --query --query_field=email "${URL}")
BRANCH=$(git branch --show-current)
INVALID=$(urlp --query --query_field=invalid "${URL}")

if [[ ${EMAIL} ]]; then
  TITLE="ONTIE ${BRANCH}"
  if [[ ${EMAIL} =~ ${EMAIL_PAT} ]]; then
	echo "<div class='alert alert-primary'>Creating a Google Sheet and sharing it with ${EMAIL}...</div>"
    cogs init -t "${TITLE}" -u ${EMAIL} -r writer
    make load push
  else
    echo '<meta http-equiv="refresh" content="0; ?invalid=true"/>'
  fi
fi

if [ -d .cogs ]; then
  LINK=$(cogs open)
  echo "<meta http-equiv='refresh' content='0; ${LINK}'/>"
  exit 0
fi

if [[ ${INVALID} ]]; then
  echo '<div class="alert alert-danger">Invalid email entered. Please try again.</div>'
fi
echo '<p>Please provide your Google Account name, so we can create and share a Google Sheet with you.</p>'
echo '<form action="">'
echo 'Google account (email):'
echo '<input name="email" type="text"/>'
echo '<input type="submit"/>'
echo '</form>'
