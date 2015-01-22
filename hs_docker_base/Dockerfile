FROM ubuntu

RUN apt-get update
RUN apt-get install -y python2.7-mapnik python2.7-scipy python2.7-numpy python2.7-psycopg2 cython python2.7-pysqlite2
RUN apt-get install -y nodejs npm python-virtualenv
RUN apt-get install -y postgresql-9.3 postgresql-client-common postgresql-common postgresql-client-9.3 redis-tools
RUN apt-get install -y sqlite3 sqlite3-pcre libspatialite-dev libspatialite5 spatialite-bin
RUN apt-get install -y ssh git libfreetype6 libfreetype6-dev libxml2-dev libxslt-dev libprotobuf-dev
RUN apt-get install -y python2.7-gdal gdal-bin libgdal-dev gdal-contrib python-pillow protobuf-compiler libtokyocabinet-dev tokyocabinet-bin libreadline-dev ncurses-dev
RUN apt-get install -y docker.io

ADD . /home/docker

WORKDIR /home/docker/pysqlite-2.6.3/
RUN python setup.py install
RUN pip install cython
RUN pip install numexpr

WORKDIR /home/docker
RUN pip install -r requirements.txt

WORKDIR  /home/docker
RUN apt-get install -y curl
RUN curl -O http://www.hdfgroup.org/ftp/HDF5/prev-releases/hdf5-1.8.13/src/hdf5-1.8.13.tar.gz
RUN curl -O ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.3.2.tar.gz
RUN curl -O https://pypi.python.org/packages/source/n/netCDF4/netCDF4-1.1.1.tar.gz
RUN tar -xvzf hdf5-1.8.13.tar.gz
RUN tar -xvzf netcdf-4.3.2.tar.gz
RUN tar -xvzf netCDF4-1.1.1.tar.gz

WORKDIR /home/docker/hdf5-1.8.13
RUN ./configure --prefix=/usr/local --enable-shared --enable-hl
RUN make
RUN sudo make install

WORKDIR /home/docker/netcdf-4.3.2
RUN LDFLAGS=-L/usr/local/lib CPPFLAGS=-I/usr/local/include ./configure --enable-netcdf-4 --enable-dap --enable-shared --prefix=/usr/local
RUN make
RUN sudo make install

WORKDIR /home/docker/netCDF4-1.1.1
RUN python setup.py install

RUN useradd -m docker -g docker
RUN echo docker:docker | chpasswd
