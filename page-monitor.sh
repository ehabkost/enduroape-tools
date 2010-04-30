#!/bin/bash

# crontab: */15 * * * * monitor.sh usuario senha

targets="caio1982 olavojunior botobr julianolf tiagosh drjackstraw"
message="TRILHAPE ETAPA ALERT, novas infos -> http://www.trilhape.com.br/etapas.php"

lynx -dump --nolist http://www.trilhape.com.br/etapas.php | sed '/das Etapas$/,/EMBED/!d' > /tmp/new

diff -ruN /tmp/old /tmp/new
if [ $? = 1 ]; then
	mv -f /tmp/new /tmp/old
	for user in ${targets}; do
		sleep 5 && curl -u ${1}:${2} --data "user=${user}" --data "text=${message}" http://twitter.com/direct_messages/new.xml
	done
fi

exit 0