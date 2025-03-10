FROM hydroshare/hs_docker_base:fe9c4f4
# make sure to update multistage-node dockerfile as well if you update this base image

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen


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

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
