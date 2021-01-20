npm run build

cp ./build/css/app*.css ./deploy/css/app.css
cp ./build/css/chunk-vendors*.css ./deploy/css/chunk-vendors.css
cp ./build/css/*.css ./deploy/css
cp ./build/js/app*.js ./deploy/js/app.js
cp ./build/js/*.js ./deploy/js
cp ./build/map.js ./deploy/js/map.js
cp ./build/js/*.map ./deploy/js/
cp ./build/js/chunk-vendors*.js ./deploy/js/chunk-vendors.js
docker exec -it hydroshare python manage.py collectstatic --no-input
