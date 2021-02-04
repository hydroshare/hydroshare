#!/bin/sh
set -x

# create nginx user/group first, to be consistent throughout docker variants
addgroup --system --gid 101 nginx 
adduser --system --disabled-login --disabled-password --ingroup nginx --home /home/nginx --gecos "nginx user" --uid 101 nginx \

# Add contrib modules, which is the only way to compile anything! 
cd /etc/apt
sed -e "s/main/main contrib non-free/" < sources.list > sources.new
mv sources.new sources.list 
apt update 
cd /

# This is a union of the tools needed by NGINX and this script
apt-get install -y \
    gcc \
    gpg \
    git \
    curl \
    make \
    gzip \
    tar \
    vim \
    libssl-dev \
    libpcre3-dev \
    zlib1g-dev \
    libxml2-dev \
    libxslt-dev \
    libgd-dev \
    libgeoip-dev \
    libperl-dev

# Install GPG keys
gpg --import /usr/src/nginx.key

CONFIG="\
        --prefix=/etc/nginx \
        --sbin-path=/usr/sbin/nginx \
        --modules-path=/usr/lib/nginx/modules \
        --conf-path=/etc/nginx/nginx.conf \
        --error-log-path=/var/log/nginx/error.log \
        --http-log-path=/var/log/nginx/access.log \
        --pid-path=/var/run/nginx.pid \
        --lock-path=/var/run/nginx.lock \
        --http-client-body-temp-path=/var/cache/nginx/client_temp \
        --http-proxy-temp-path=/var/cache/nginx/proxy_temp \
        --http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp \
        --http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp \
        --http-scgi-temp-path=/var/cache/nginx/scgi_temp \
        --user=nginx \
        --group=nginx \
        --with-http_ssl_module \
        --with-http_realip_module \
        --with-http_addition_module \
        --with-http_sub_module \
        --with-http_dav_module \
        --with-http_flv_module \
        --with-http_mp4_module \
        --with-http_gunzip_module \
        --with-http_gzip_static_module \
        --with-http_random_index_module \
        --with-http_secure_link_module \
        --with-http_stub_status_module \
        --with-http_auth_request_module \
        --with-http_xslt_module=dynamic \
        --with-http_image_filter_module=dynamic \
        --with-http_geoip_module=dynamic \
        --with-http_perl_module=dynamic \
        --with-threads \
        --with-stream \
        --with-stream_ssl_module \
        --with-http_slice_module \
        --with-mail \
        --with-mail_ssl_module \
        --with-file-aio \
        --with-http_v2_module \
        --add-module=/usr/src/progress/nginx-upload-progress-module-master \
        --add-module=/usr/src/upload/nginx-upload-module \
    "
curl -fSL http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz -o nginx.tar.gz
curl -fSL http://nginx.org/download/nginx-$NGINX_VERSION.tar.gz.asc  -o nginx.tar.gz.asc
gpg --batch --verify nginx.tar.gz.asc nginx.tar.gz
export GNUPGHOME="$(mktemp -d)"
rm -r "$GNUPGHOME" nginx.tar.gz.asc
mkdir -p /usr/src
tar -zxC /usr/src -f nginx.tar.gz
rm nginx.tar.gz
mkdir -p /usr/src/upload
cd /usr/src/upload
git clone https://github.com/vkholodkov/nginx-upload-module.git
cd nginx-upload-module
git checkout 2.255
mkdir -p /usr/src/progress
cd /usr/src/progress
curl -fSLO https://github.com/masterzen/nginx-upload-progress-module/archive/master.zip
unzip master.zip
cd /usr/src/nginx-$NGINX_VERSION
./configure $CONFIG --with-debug
make -j$(getconf _NPROCESSORS_ONLN)
mv objs/nginx objs/nginx-debug
mv objs/ngx_http_xslt_filter_module.so objs/ngx_http_xslt_filter_module-debug.so
mv objs/ngx_http_image_filter_module.so objs/ngx_http_image_filter_module-debug.so
mv objs/ngx_http_geoip_module.so objs/ngx_http_geoip_module-debug.so
mv objs/ngx_http_perl_module.so objs/ngx_http_perl_module-debug.so
./configure $CONFIG
make -j$(getconf _NPROCESSORS_ONLN)
make install
rm -rf /etc/nginx/html/
mkdir -p /etc/nginx/conf.d/
mkdir -p /usr/share/nginx/html/
install -m644 html/index.html /usr/share/nginx/html/
install -m644 html/50x.html /usr/share/nginx/html/
install -m755 objs/nginx-debug /usr/sbin/nginx-debug
install -m755 objs/ngx_http_xslt_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_xslt_filter_module-debug.so
install -m755 objs/ngx_http_image_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_image_filter_module-debug.so
install -m755 objs/ngx_http_geoip_module-debug.so /usr/lib/nginx/modules/ngx_http_geoip_module-debug.so
install -m755 objs/ngx_http_perl_module-debug.so /usr/lib/nginx/modules/ngx_http_perl_module-debug.so
ln -s ../../usr/lib/nginx/modules /etc/nginx/modules
strip /usr/sbin/nginx*
strip /usr/lib/nginx/modules/*.so
rm -rf /usr/src/nginx-$NGINX_VERSION
rm -rf /usr/src/upload
rm -rf /usr/src/progress

# Bring in gettext so we can get `envsubst`, then throw
# the rest away. To do this, we need to install `gettext`
# then move `envsubst` out of the way so `gettext` can
# be deleted completely, then move `envsubst` back.
apt-get install -y gettext
mv /usr/bin/envsubst /tmp/

runDeps="$(
    scanelf --needed --nobanner /usr/sbin/nginx /usr/lib/nginx/modules/*.so /tmp/envsubst \
        | awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
        | sort -u \
        | xargs -r apt info --installed \
        | sort -u \
)"

apt-get install -y $runDeps
# apt remove -y .gettext
mv /tmp/envsubst /usr/local/bin/

# forward request and error logs to docker log collector
# ln -sf /dev/stdout /var/log/nginx/access.log
# ln -sf /dev/stderr /var/log/nginx/error.log
