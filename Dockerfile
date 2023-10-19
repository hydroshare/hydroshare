FROM hydroshare/hs_docker_base:2.2.10

# Set the locale. TODO - remove once we have a better alternative worked out
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen

RUN pip install django-cachalot
RUN pip install django-redis
RUN pip install spam_patterns@git+https://github.com/CUAHSI/spam_patterns.git@0.0.4

RUN pip install django-silk

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

USER root
WORKDIR /hydroshare

CMD ["/bin/bash"]
