FROM solr:6.6

WORKDIR /opt/solr

USER $SOLR_USER

RUN chown -R $SOLR_USER:$SOLR_GROUP /opt/solr
RUN ["mkdir", "/opt/solr/server/solr/collection1"]
RUN ["mkdir", "/opt/solr/server/solr/collection1/conf"]
RUN ["mkdir", "/opt/solr/server/solr/index"]

RUN rm -f /opt/solr/server/solr/configsets/basic_configs/conf/managed-schema

ADD ./conf_solr/core.properties /opt/solr/server/solr/collection1/core.properties
ADD ./conf_solr/schema.xml.nogitignore /opt/solr/server/solr/configsets/basic_configs/conf/schema.xml
ADD ./conf_solr/solrconfig.xml /opt/solr/server/solr/collection1/conf/solrconfig.xml
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["solr-foreground"]
