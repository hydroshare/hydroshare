npm run build
rm static/css/*.css
rm static/js/*.js
rm static/js/*.map
mkdir -p static/css
mkdir -p static/js
cp templates/hs_discover/css/app*.css static/css/app.css
cp templates/hs_discover/css/chunk-vendors*.css static/css/chunk-vendors.css
cp templates/hs_discover/css/*.css static/css
cp templates/hs_discover/js/app*.js static/js/app.js
cp templates/hs_discover/js/*.js static/js
cp templates/hs_discover/map.js static/js/map.js
cp templates/hs_discover/js/*.map static/js/
cp templates/hs_discover/js/chunk-vendors*.js static/js/chunk-vendors.js
docker exec -it hydroshare python manage.py collectstatic --no-input
