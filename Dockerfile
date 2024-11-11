FROM hydroshare/hs_docker_base:262c2ca
# make sure to update multistage-node dockerfile as well if you update this base image

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN pip install psycopg==3.1.*
RUN pip install django==4.2.*
RUN pip install djangorestframework==3.14.*
RUN pip install django-haystack==3.2.*
RUN pip install drf-yasg==1.21.*
RUN pip install django-robots==6.1
RUN pip install django-autocomplete-light==3.11.*
RUN pip install django-widget-tweaks==1.5.*
RUN pip install django-crispy-forms==2.1
RUN pip install crispy-bootstrap3==2024.1
RUN pip install Mezzanine==6.0.0
RUN pip install git+https://github.com/CUAHSI/django-tus.git@2aac2e7c0e6bac79a1cb07721947a48d9cc40ec8

# intentionally keep bleach at https://github.com/mozilla/bleach/releases/tag/v5.0.1
# due to issue with mezzanine 6.0.0
# https://github.com/stephenmcd/mezzanine/issues/2054
RUN pip install bleach==5.0.1

# https://www.digicert.com/kb/digicert-root-certificates.htm
# Get the .pem file from digicert and add it to the bundle used by certifi
# Could also use the REQUESTS_CA_BUNDLE environment variable to point to the .pem file
# This was needed beacause the certifi release 
# 2024.02.02 https://github.com/certifi/python-certifi/releases/tag/2024.02.02
# does not include the GeoTrust TLS RSA CA G1 certificate at the time of this writing
# More info: https://requests.readthedocs.io/en/latest/user/advanced/#ca-certificates
RUN wget -O /usr/lib/ssl/certs/GeoTrustTLSRSACAG1.crt.pem https://cacerts.digicert.com/GeoTrustTLSRSACAG1.crt.pem && \
    update-ca-certificates && \
    cat /usr/lib/ssl/certs/GeoTrustTLSRSACAG1.crt.pem >> $(python -c "import requests; print(requests.certs.where())")

RUN pip install hsmodels==1.0.4

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
