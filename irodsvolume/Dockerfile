FROM debian:jessie
RUN apt-get update
RUN apt-get install -y curl libfuse2
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.8/ubuntu14/irods-runtime-4.1.8-ubuntu14-x86_64.deb -o irods-runtime.deb
RUN curl ftp://ftp.renci.org/pub/irods/releases/4.1.8/ubuntu14/irods-icommands-4.1.8-ubuntu14-x86_64.deb -o irods-icommands.deb
RUN dpkg -i irods-runtime.deb irods-icommands.deb
RUN apt-get -f -y install
RUN rm irods-runtime.deb irods-icommands.deb
COPY iinit.input iinit.input
USER root
RUN rm -rf ~/.irods/
RUN cat iinit.input | iinit
VOLUME [ "/irodsmnt" ]
ENTRYPOINT [ "irodsFs", "-d", "/irodsmnt/" ]
