#!/bin/bash

#Post-build script to change local paths of folders in order to re-route all specified folder paths to within the report directory
cd ../

sed -i -r 's,\/reports\/build\/index.html,/vger/vger-tools/reports/build/index.html,g' app.routes.js
#remove old file
rm app.routes.js-r

cd reports/build

sed -i -r 's,static\/js\/main.,/vger/vger-tools/reports/build/static/js/main.,g' asset-manifest.json
#remove old file
rm asset-manifest.json-r

#also reroute non-main instances that index.html uses
sed -i -r 's,\/reports\/build,/vger/vger-tools/reports/build,g' index.html
#remove old file
rm index.html-r

sed -i -r 's,\/static\/js,vger-tools/reports/build/static/js,g' index.html
#remove old file
rm index.html-r

sed -i -r 's,static\/js\/main.,/vger/vger-tools/reports/build/static/js/main.,g' service-worker.js
#remove old file
rm service-worker.js-r

cd static/js

files=( *.map )

sed -i -r 's,static\/js\/main.,vger/vger-tools/reports/build/static/js/main.,g' ${files[0]}
#remove old file
rm ${files[0]}-r
