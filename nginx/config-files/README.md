These files include the configuration for the NGINX inner proxy that runs next to Django. 
* hydroshare-local-nginx.conf.template is a template just for development 
* hydroshare-nginx.conf.template does not invoke ssl or other production features. 
* hydroshare-ssl-nginx.conf.template is the site configuration for production. 
* nginx.conf-default.template is the overall configuration for all instances. 

When changing these files, it is really important to copy them into /projects/hydroshare/hsdata/zdt into the appropriate 
deploy directory. Otherwise, they will be erroniously overwritten during deploy. 

When you run-nginx, these are copied and edited into the runtime images, include: 
* hs-nginx.conf: the site configuration. 
* nginx.conf-default: the server configuration

The configuration for the outer proxy server in production is now contained in ../hs_proxy_home
