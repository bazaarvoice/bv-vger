#!/bin/bash

#Post-deploy script to change back local paths of folders in order to run in local environments
cd ../

sed -i -r 's,vger\/vger-tools\/reports\/build\/index.html,reports/build/index.html,g' app.routes.js
#remove old file
rm app.routes.js-r

cd reports/build

sed -i -r 's,vger\/vger-tools\/reports\/build\/static\/js\/main.,reports/build/static/js/main.,g' asset-manifest.json
#remove old file
rm asset-manifest.json-r

sed -i -r 's,vger-tools\/reports\/build\/static\/js,/reports/build/static/js,g' index.html
#remove old file
rm index.html-r

#also reroute non-main instances that index.html uses
sed -i -r 's,\/vger\/vger-tools\/reports\/build,/reports/build,g' index.html
#remove old file
rm index.html-r

sed -i -r 's,vger\/vger-tools\/reports\/build\/static\/js\/main.,reports/build/static/js/main.,g' service-worker.js
#remove old file
rm service-worker.js-r

cd static/js

files=( *.map )

sed -i -r 's,vger\/vger-tools\/reports\/build\/static\/js\/main.,reports/build/static/js/main.,g' ${files[0]}
#remove old file
rm ${files[0]}-r