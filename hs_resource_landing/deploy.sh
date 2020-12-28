npm run build
rm static/css/*.css
rm static/js/*.js
rm static/js/*.map
mkdir -p static/css
mkdir -p static/js
cp templates/hs_resource_landing/css/app*.css static/css/app.css
cp templates/hs_resource_landing/css/chunk-vendors*.css static/css/chunk-vendors.css
cp templates/hs_resource_landing/css/*.css static/css
cp templates/hs_resource_landing/js/app*.js static/js/app.js
cp templates/hs_resource_landing/js/*.js static/js
cp templates/hs_resource_landing/js/*.map static/js/
cp templates/hs_resource_landing/js/chunk-vendors*.js static/js/chunk-vendors.js
docker exec -it hydroshare python manage.py collectstatic --no-input
