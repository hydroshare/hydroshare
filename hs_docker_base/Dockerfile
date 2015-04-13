FROM ubuntu

RUN apt-get update
RUN apt-get install -y python2.7-mapnik python2.7-scipy python2.7-numpy python2.7-psycopg2 cython python2.7-pysqlite2
RUN apt-get install -y nodejs npm python-virtualenv
RUN apt-get install -y postgresql-9.3 postgresql-client-common postgresql-common postgresql-client-9.3 redis-tools
RUN apt-get install -y sqlite3 sqlite3-pcre libspatialite-dev libspatialite5 spatialite-bin
RUN apt-get install -y ssh git libfreetype6 libfreetype6-dev libxml2-dev libxslt-dev libprotobuf-dev
RUN apt-get install -y python2.7-gdal gdal-bin libgdal-dev gdal-contrib python-pillow protobuf-compiler libtokyocabinet-dev tokyocabinet-bin libreadline-dev ncurses-dev
RUN apt-get install -y docker.io
RUN apt-get install -y curl

# install nco, ncdump, ncgen
RUN apt-get install -y nco
RUN apt-get install -y netcdf-bin

ADD . /home/docker

WORKDIR /home/docker/pysqlite-2.6.3/
RUN python setup.py install
RUN pip install numexpr==2.4

WORKDIR /home/docker
RUN pip install -r requirements.txt

# install netcdf4 python
WORKDIR  /home/docker
RUN curl -O https://pypi.python.org/packages/source/n/netCDF4/netCDF4-1.1.1.tar.gz
RUN tar -xvzf netCDF4-1.1.1.tar.gz
WORKDIR /home/docker/netCDF4-1.1.1
RUN python setup.py install
# Cleanup NetCDF install files
WORKDIR /home/docker
RUN rm netCDF4-1.1.1.tar.gz

RUN useradd -m docker -g docker
RUN echo docker:docker | chpasswd