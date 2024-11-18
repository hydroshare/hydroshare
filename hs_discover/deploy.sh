npm run build
rm -rf static/css
rm -rf static/js
mkdir -p static/css
mkdir -p static/js
cp templates/hs_discover/css/*.css static/css
cp templates/hs_discover/js/*.js static/js
cp templates/hs_discover/map.js static/js/map.js
docker exec -it hydroshare python manage.py collectstatic --no-input
