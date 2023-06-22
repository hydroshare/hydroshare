npm run build
rm static/css/*.css
rm static/js/*.js
rm static/js/*.map
mkdir -p static/css
mkdir -p static/js
cp templates/hs_discover/css/* static/css/
cp templates/hs_discover/js/* static/js/
cp templates/hs_discover/map.js static/js/map.js
docker exec -it hydroshare python manage.py collectstatic --no-input
