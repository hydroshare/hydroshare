FROM mjstealey/irods-provider-postgres:4.2.4

RUN useradd -m -p hsuserproxy -s /bin/bash hsuserproxy
RUN useradd -m -p rods -s /bin/bash rods
RUN mkdir -p /home/hsuserproxy/.irods
COPY ./conf_irods/users.local.org/irods_environment.json /root/.irods/irods_environment.json
COPY ./irods/delete_user.sh /home/hsuserproxy/delete_user.sh
COPY ./irods/create_user.sh /home/hsuserproxy/create_user.sh

RUN chmod -R 777 /home
