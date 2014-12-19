<?xml version="1.0" encoding="UTF-8"?>
<!-- Created with Liquid XML Studio Developer Edition (Education) 9.0.11.3078 (http://www.liquid-technologies.com) -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:wml2="http://www.opengis.net/waterml/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:wml="http://www.cuahsi.org/waterML/1.1/"
    xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:om="http://www.opengis.net/om/2.0" xmlns:swe="http://www.opengis.net/swe/2.0"
    xmlns:op="http://schemas.opengis.net/op" xmlns:sf="http://www.opengis.net/sampling/2.0"
    xmlns:sams="http://www.opengis.net/samplingSpatial/2.0"
    xmlns:sam="http://www.opengis.net/sampling/2.0"
    xmlns:wml1_0="http://www.cuahsi.org/waterML/1.0/" xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:gmd="http://www.isotc211.org/2005/gmd" xmlns:gco="http://www.isotc211.org/2005/gco"
    xmlns:gss="http://www.isotc211.org/2005/gss" version="2.0">
    <!-- exclude-result-prefixes="xs" -->
    <!-- need to import because this also has a wml:timeSeriesResponse template -->
    <xsl:import href="WaterML1_1_timseries_WaterProcess_to_WaterML2.xsl"/>
    <xsl:import href="WaterML1_1_timseries_ObservedProperty_to_WaterML2.xsl"/>
    <xsl:import href="WaterML_1_1_source_to_waterML2_identification.xsl"/>
    <xsl:import href="WaterML1_1_site_to_WaterML2.xsl"/>
    <xsl:import href="WaterML1_1_common_to_waterml2.xsl"/>

    <xsl:include href="fxsl-1.2/split.xsl"/>
    
    <xsl:param name="foiInline">false</xsl:param>
    <xsl:param name="wfsBase">(Provide.wfsBase.Endpoint)</xsl:param>
    <xsl:param name="observedPropertiesBase">(Provide.observedPropertiesBase.endpoint )</xsl:param>
    <xsl:param name="wqxBase">(Provide.wqxBase.Endpoint)</xsl:param>
    <xsl:param name="concept">(provide.concept)</xsl:param>
    <xsl:param name="generationdate">2011-01-01T00:00:00Z</xsl:param>
    <xsl:param name="generationSystem">XSLT Translation from WaterML1.1 response
        document</xsl:param>

    <xsl:param name="defaultInterpoloationType">2011-01-01T00:00:00Z</xsl:param>
<xsl:param name="comments">false</xsl:param>

    <xsl:output method="xml" indent="yes" omit-xml-declaration="no"/>

    <!-- this assumes that the codes are unique for a file. ok since it comes from an ODM -->
    <xsl:key name="qualifiers" match="wml:qualifier" use="wml:qualifierCode"/>
    <xsl:key name="variables" match="wml:variable" use="wml:variableCode"/>
    <xsl:key name="qclevel" match="wml:timeSeries/wml:values/wml:qualityControlLevel"
        use="wml:qualityControlLevelCode"/>
    <xsl:key name="censorCode" match="wml:timeSeries/wml:values/wml:censorCode" use="wml:censorCode"/>
    <xsl:key name="methodCode" match="wml:timeSeries/wml:values/wml:method" use="wml:methodCode"/>
    <xsl:key name="methodID" match="wml:timeSeries/wml:values/wml:method" use="@methodID"/>
    <xsl:key name="siteCode" match="wml:timeSeries/wml:sourceInfo" use="wml:siteCode"/>
    <xsl:key name="offset" match="wml:timeSeries/wml:values/wml:offset" use="wml:offsetTypeCode"/>
   
    <xsl:include  href="./WaterML_1_1_to_WaterML2_dictionaries.xsl" />
    
    <xsl:template match="wml:timeSeriesResponse">
        <wml2:Collection>
            <xsl:attribute name="xsi:schemaLocation">http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd</xsl:attribute>
             
            <xsl:attribute name="gml:id">generated_collection_doc</xsl:attribute>
            <!-- Get a unique list of all the quality codes used in the time series to build up a dict -->
            <xsl:variable name="unique-list"
                select="wml:timeSeries/wml:values/wml:value/@qualityControlLevel[not(.=following::wml:value/@qualityControlLevel)]"/>
            <wml2:metadata>
                <wml2:DocumentMetadata>
                    <xsl:attribute name="gml:id">doc_md</xsl:attribute>
                    <wml2:generationDate>
                        <xsl:value-of select="$generationdate"/>
                    </wml2:generationDate>
                    <wml2:version xlink:href="http://www.opengis.net/waterml/2.0"
                        xlink:title="WaterML 2.0 RFC"/>
                    <wml2:generationSystem>
                        <xsl:value-of select="$generationSystem"/>
                    </wml2:generationSystem>

                </wml2:DocumentMetadata>

            </wml2:metadata>

            <!-- ====================
                ADD LOCAL DICTIONARIES 
            In WaterML_1_1_to_WaterML2_dictionaries.xsl
            =========================== -->
            <xsl:call-template name="localDictVaraible" />
            <xsl:call-template name="localDictQualifier" />
            <xsl:call-template name="localDictQCLevel" />   
            <xsl:call-template name="localDictCensorCode" />
            <xsl:call-template name="localDictMethod" />
            <xsl:call-template name="localDictOffset" />
            

    

            <!-- ====================
                list of sampling features 
            ====================-->

            <!-- this may break with dataSetInfo -->
            <xsl:for-each
                select="//wml:timeSeries/wml:sourceInfo[generate-id(.) =
                generate-id(key('siteCode',  wml:siteCode)[1])] ">
                <wml2:samplingFeatureMember>
                    <!-- xslt 2    <xsl:if test="ends-with(../wml:sourceInfo/@xsi:type,'SiteInfoType')">
                              -->

                    <xsl:call-template name="SiteInfoToWaterObservationPoint">
                        <xsl:with-param name="sourceInfoType" select="../wml:sourceInfo"
                        > </xsl:with-param>
                    </xsl:call-template>
                </wml2:samplingFeatureMember>
            </xsl:for-each>
          

            <!-- ====================
                           ObservationMember (aka timeseries 
                       ====================== -->
            <xsl:for-each select="wml:timeSeries/wml:values">
                <wml2:observationMember>
                    <xsl:variable name="obsMemberNumber" select="position()"/>
                    <om:OM_Observation>
                        <!-- may change -->

                        <xsl:attribute name="gml:id">
                            <xsl:choose>
                                <xsl:when test="@name">
                                    <xsl:value-of select="@name"/>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:value-of select="concat('observation-',$obsMemberNumber)"/>
                                </xsl:otherwise>
                            </xsl:choose>

                        </xsl:attribute>

                        <!-- ====================
                           ObservationMetadata 
                       ====================== -->
                        <xsl:if
                            test="(count(wml:source) >0)
                            or
                            (../wml:variable/wml:sampleMedium)">
                            <om:metadata>
                                <wml2:ObservationMetadata>
<xsl:choose>
    <xsl:when test="count(wml:source) >0">
                                <!--        <xsl:call-template name="identificationInfo">
                                            <xsl:with-param name="source" select="wml:source[1]"/>
                                        </xsl:call-template>
                                   -->     
        <xsl:call-template name="sourceToMetadata">
          <xsl:with-param name="sources" select="wml:source"></xsl:with-param>   
        </xsl:call-template> 
    </xsl:when>
<xsl:otherwise>
    <!-- needed  to create a valid Metadata record -->
    <gmd:contact gco:nilReason="missing"/>
    <gmd:dateStamp gco:nilReason="inapplicable"/>
    <gmd:identificationInfo gco:nilReason="unknown"/>
</xsl:otherwise>
 </xsl:choose>                                   <!-- +observation meatadata 9.3.1
        intendedSamplingInterval>
            status
            sampledMedium
            maximumGap
          parameter
          -->
                                    <xsl:if test="$comments = 'true' ">
                                    <xsl:comment>wml2:intendedSamplingInterval</xsl:comment>
                                    <xsl:comment>  wml2:status should be a mapping based on QC level... but there is no fixed qcvocab</xsl:comment>
                                    <!--  
                                      <wml2:status xlink:title="Unknown"></wml2:status>
                                   -->
                                    </xsl:if>
                                    <xsl:if test="../wml:variable/wml:sampleMedium">
                                        <!-- list of mappings in common -->
                                        <xsl:call-template name="SampleMediumMapper">
                                            <xsl:with-param name="SampleMedium"
                                                select="../wml:variable/wml:sampleMedium"/>
                                        </xsl:call-template>
                                    </xsl:if>
                                    <xsl:if test="$comments = 'true' ">
                                        <xsl:comment>wml2:maximumGap</xsl:comment>
                                    </xsl:if>
                                </wml2:ObservationMetadata>
                            </om:metadata>
                        </xsl:if>
                        <!-- ====================
                           END ObservationMetadata 
                       ====================== -->

                        <!-- Figure out the start and end time of the series -->
                        <xsl:variable name="start-time" select="wml:value[1]/@dateTime"> </xsl:variable>
                        <xsl:variable name="end-time" select="wml:value[last()]/@dateTime"> </xsl:variable>

                        <om:phenomenonTime>
                            <!-- gml:ids will need to be generated when more than one series as have to be unique in document -->
                            <gml:TimePeriod>
                                <xsl:attribute name="gml:id">
                                    <xsl:value-of select="concat('phen_time-',$obsMemberNumber)"/>
                                </xsl:attribute>
                                <gml:beginPosition>
                                    <xsl:value-of select="$start-time"> </xsl:value-of>
                                </gml:beginPosition>
                                <gml:endPosition>
                                    <xsl:value-of select="$end-time"> </xsl:value-of>
                                </gml:endPosition>
                            </gml:TimePeriod>
                        </om:phenomenonTime>
                        <om:resultTime>
                            <gml:TimeInstant>
                                <xsl:attribute name="gml:id">
                                    <xsl:value-of select="concat('eor-',$obsMemberNumber)"/>
                                </xsl:attribute>

                                <gml:timePosition>
                                    <xsl:value-of select="$end-time"> </xsl:value-of>
                                </gml:timePosition>
                            </gml:TimeInstant>
                        </om:resultTime>
                        <om:procedure>
                            <xsl:call-template name="WaterObservationProcess"/>
                        </om:procedure>
                        <!-- observedProperty needs to be the concept. If no concept, then original variable code-->
                        <!-- This feature-property that provides the (semantic) type of the observation. 	
                      The description of the phenomenon may be quite specific and constrained.
                      The description of the property-type may be presented using various alternative encodings. 							If shown inline, the swe:Phenomenon schema is required. 		
                      -->

                        <!--
                        <xsl:comment>om parameter</xsl:comment>
                        -->
                        
                        <om:observedProperty>
                            <xsl:attribute name="xlink:href">
                               <xsl:text>#</xsl:text>
                                <xsl:call-template name="VariableIdentifier">
                                    <xsl:with-param name="variable" select="../wml:variable"></xsl:with-param>
                                </xsl:call-template>
                            <!--     <xsl:value-of
                                    select="concat('#',../wml:variable/wml:variableCode[1]/@vocabulary,'-',../wml:variable/wml:variableCode[1])"/>
                                  <xsl:value-of
                                    select="concat('#','variableCode-',$concept)"
                                />
                                -->
                            </xsl:attribute>
                            <xsl:attribute name="xlink:title">
                                <xsl:call-template name="HisOntologyMapper">
                                    <xsl:with-param name="VariableCode" select="concat(../wml:variable/wml:variableCode[1]/@vocabulary,':', ../wml:variable/wml:variableCode)"></xsl:with-param>
                                </xsl:call-template>
                            </xsl:attribute>
                            <!--      <xsl:call-template name="ObservedProperty">
                          <xsl:with-param name="concept"><xsl:value-of select="$concept"/></xsl:with-param>
                          <xsl:with-param name="observedPropertiesBase"><xsl:value-of select="$observedPropertiesBase"/></xsl:with-param>
                        </xsl:call-template>
                        -->
                        </om:observedProperty>

                        <om:featureOfInterest>
                            <xsl:choose>

                                <xsl:when
                                    test="substring(../wml:sourceInfo/@xsi:type, string-length(../wml:sourceInfo/@xsi:type)-11) ='SiteInfoType'">
                                    <xsl:attribute name="xlink:href">
                                        <xsl:text>#</xsl:text>
                                        <xsl:call-template name="SiteIdentifier">
                                            <xsl:with-param name="site" select="../wml:sourceInfo"/>
                                        </xsl:call-template>
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="../wml:sourceInfo/@xsi:type='DataSetInfoType'">
                                    <xsl:attribute name="xlink:href">
                                        <xsl:value-of
                                            select="../wml:sourceInfo/wml:dataSetIdentifier"/>
                                    </xsl:attribute>
                                </xsl:when>
                            </xsl:choose>

                            <xsl:choose>

                                <xsl:when
                                    test="substring(../wml:sourceInfo/@xsi:type, string-length(../wml:sourceInfo/@xsi:type)-11) ='SiteInfoType'">
                                    <xsl:attribute name="xlink:title">
                                        <xsl:value-of
                                            select="concat(../wml:sourceInfo/wml:siteName,../wml:sourceInfo/wml:siteCode)"
                                        />
                                    </xsl:attribute>
                                </xsl:when>
                                <xsl:when test="../wml:sourceInfo/@xsi:type='DataSetInfoType'">
                                    <xsl:attribute name="xlink:title">
                                        <xsl:value-of select="../wml:sourceInfo/wml:dataSetName"/>
                                    </xsl:attribute>
                                </xsl:when>
                            </xsl:choose>
                        </om:featureOfInterest>
                        <xsl:if test="$comments = 'true' ">
                        <xsl:comment>9.3.1.5 resultQuality would go here</xsl:comment>
                      </xsl:if>
                        <xsl:choose>
                            <xsl:when test="../wml:timeSeries/wml:variable/wml:categories">
                                <xsl:call-template name="categoricalTimeSeries">
                                    <xsl:with-param name="obsMemberNumber" select="$obsMemberNumber"
                                    />
                                </xsl:call-template>
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:call-template name="measurementTimeSeries">
                                    <xsl:with-param name="obsMemberNumber" select="$obsMemberNumber"
                                    />
                                </xsl:call-template>
                            </xsl:otherwise>
                        </xsl:choose>
                    </om:OM_Observation>
                </wml2:observationMember>
            </xsl:for-each>
        </wml2:Collection>
    </xsl:template>
    <xsl:template name="categoricalTimeSeries">
        <xsl:param name="obsMemberNumber"/>
        <xsl:comment>not yet implemented</xsl:comment>
    </xsl:template>

    <xsl:template name="measurementTimeSeries">
        <xsl:param name="obsMemberNumber"/>
        <om:result>
            <wml2:MeasurementTimeseries>
                <xsl:attribute name="gml:id">
                    <xsl:value-of select="concat(../wml:timeSeries/@name,'_TS-',position() )"
                    > </xsl:value-of>
                </xsl:attribute>
               
                <wml2:metadata>
                    <wml2:MeasurementTimeseriesMetadata>
                        <xsl:if test="$comments = 'true' ">
                            <xsl:comment>domainExtent refers to time described
                                               above</xsl:comment>
                        </xsl:if>
                        <wml2:temporalExtent>
                               <xsl:attribute name="xlink:href">
                                   <xsl:value-of select="concat('#phen_time-',$obsMemberNumber)"/>
                               </xsl:attribute>
                           </wml2:temporalExtent>
                        <xsl:call-template name="TimeSeriesMetadata"/>
                    </wml2:MeasurementTimeseriesMetadata>
                </wml2:metadata>



                <wml2:defaultPointMetadata>
                    <wml2:DefaultTVPMeasurementMetadata>
                        <xsl:call-template name="TVPMetadataDefault"/>

                    </wml2:DefaultTVPMeasurementMetadata>
                </wml2:defaultPointMetadata>



                <xsl:for-each select="wml:value">

                    <wml2:point>
                        <wml2:MeasurementTVP>
                            <wml2:time>
                                <xsl:choose>
                                    <xsl:when
                                        test="string-length(@dateTime) = 29 or contains(@dateTime,'+')  or contains(@dateTime,'Z') or contains(substring(@dateTime, 23),'-')">
                                        <xsl:value-of select="@dateTime"/>
                                    </xsl:when>
                                    <xsl:when test="@timeOffset">
                                        <xsl:choose>
                                            <xsl:when
                                                test="starts-with(@timeOffset,'+') or starts-with(@timeOffset,'-')">
                                                <xsl:value-of select="concat(@dateTime,@timeOffset)"
                                                />
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <!-- not valid but hey it will be there -->
                                                <xsl:value-of select="@dateTime"/>
                                            </xsl:otherwise>

                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:when
                                        test="../../wml:sourceInfo/wml:timeZoneInfo/wml:defaultTimeZone/@zoneOffset">
                                        <xsl:variable name="zoneOffset"
                                            select="../../wml:sourceInfo/wml:timeZoneInfo/wml:defaultTimeZone/@zoneOffset"/>
                                        <xsl:choose>
                                            <xsl:when
                                                test="starts-with($zoneOffset,'+') or starts-with($zoneOffset,'-')">
                                                <xsl:value-of select="concat(@dateTime,$zoneOffset)"
                                                />
                                            </xsl:when>
                                            <xsl:otherwise>
                                                <!-- not valid but hey it will be there -->
                                                <xsl:value-of select="@dateTime"/>
                                            </xsl:otherwise>

                                        </xsl:choose>
                                    </xsl:when>
                                    <xsl:otherwise>
                                        <!-- not valid but hey it will be there -->
                                        <xsl:value-of select="@dateTime"/>
                                    </xsl:otherwise>
                                </xsl:choose>
                               <!-- <xsl:value-of select="@dateTime"/> -->
                            </wml2:time>
                            <wml2:value>
                                <xsl:value-of select="."/>
                            </wml2:value>

                            <xsl:if
                                test="count(../wml:qualityControlLevel) > 1 or 
                                count(../wml:qualifier) > 1 
                                or count(../wml:method) > 1
                                or count(../wml:censorCode) > 1
                                or count(../wml:source) >1
                                or @labSampleCode
                                or @offsetValue">
                                <wml2:metadata>
                                    <wml2:TVPMeasurementMetadata>
                                        <xsl:call-template name="TVPMetadata"/>
                                    </wml2:TVPMeasurementMetadata>
                                </wml2:metadata>
                            </xsl:if>
                        </wml2:MeasurementTVP>
                    </wml2:point>
                </xsl:for-each>

            </wml2:MeasurementTimeseries>
        </om:result>

    </xsl:template>

    <!--              </om:OM_Observation>
                </wml2:observationMember>
            </xsl:for-each>
        </wml2:Collection>
    </xsl:template>
    -->


    <xsl:template name="TimeSeriesMetadata">
        <xsl:if test="$comments = 'true' ">
            <xsl:comment>9.11.4 (TimeSeriesMetadata) + 9.14.1 (MeasurementTimeSeriesMetadata)
            basetime
                                            spacing commentblock startAnchorPoint endAnchorPoint
                                            cumulative accumulationAnchorTime
                                            accumulationIntervalLength aggregationDuration </xsl:comment>
     </xsl:if>
        <!--       <wml2:cumulative>false</wml2:cumulative> -->
        <xsl:choose>
            <xsl:when test="../wml:variable/wml:timeScale/wml:timeSupport > 0">
                <wml2:cumulative>true</wml2:cumulative>
               
            </xsl:when>
            <xsl:otherwise>
                <wml2:cumulative>false</wml2:cumulative>
            </xsl:otherwise>
        </xsl:choose>

    </xsl:template>


    <xsl:template name="TVPMetadataDefault">

        <xsl:choose>
            <xsl:when test="count(wml:censorCode) = 0 ">
                <wml2:quality>
                    <xsl:attribute name="xlink:href"
                        >http://www.opengis.net/def/waterml/2.0/quality/unchecked</xsl:attribute>
                    <xsl:attribute name="xlink:title">Unchecked</xsl:attribute>
                </wml2:quality>
            </xsl:when>

            <xsl:when test="count(wml:censorCode) = 1 ">
                <!-- there is one -->
                <xsl:call-template name="mapCensorCode">
                    <xsl:with-param name="censorCode"
                        select="wml:censorCode/wml:censorCodeDescription"/>
                </xsl:call-template>
            </xsl:when>
            <!-- otherwise moth than one. -->
        </xsl:choose>
        <xsl:if test=" count(wml:method) = 1 ">
            <wml2:qualifier>
           <!--     <xsl:attribute name="xlink:href">
                    <xsl:text>#</xsl:text>
                    <xsl:text>methodCode-</xsl:text>
                    <xsl:call-template name="MethodIdentifier">
                        <xsl:with-param name="method" select="wml:method"/>
                    </xsl:call-template>
                </xsl:attribute>
                <xsl:attribute name="xlink:role">
                    <xsl:text>http://hiscentral.cuahsi.org/wml/qualifier/method</xsl:text>
                </xsl:attribute>
                --> <xsl:variable name="aMethod">
                        <xsl:text>#</xsl:text>
                        <xsl:text>methodCode-</xsl:text>
                        <xsl:call-template name="MethodIdentifier">
                            <xsl:with-param name="method" select="wml:method"/>
                        </xsl:call-template>
                    </xsl:variable>
                <xsl:call-template name="sweText">
                   
                    <xsl:with-param name="definitionUrl" select="$aMethod"></xsl:with-param>
                <xsl:with-param name="value" select="wml:method/wml:methodDescription"></xsl:with-param>
                </xsl:call-template>
            </wml2:qualifier>
        </xsl:if>
        <xsl:if test=" count(wml:qualifier) = 1 ">
            <wml2:qualifier>
               <!-- <xsl:attribute name="xlink:href">
                    <xsl:text>#</xsl:text>
                    <xsl:call-template name="QualifierIdentifier">
                        <xsl:with-param name="qualifier" select="wml:qualifier[1]/wml:qualifierCode"></xsl:with-param>
                    </xsl:call-template>

                </xsl:attribute>
                -->
                <xsl:call-template name="sweText">
                    <xsl:with-param name="definitionUrl"><xsl:text>#</xsl:text>
                        <xsl:call-template name="QualifierIdentifier">
                            <xsl:with-param name="qualifier" select="wml:qualifier[1]/wml:qualifierCode"></xsl:with-param>
                        </xsl:call-template></xsl:with-param>
                    <xsl:with-param name="value" select="wml:qualifier[1]/wml:qualifierCode"></xsl:with-param>
                </xsl:call-template>
            </wml2:qualifier>
        </xsl:if>
        <xsl:if test="count(wml:qualityControlLevel) > 0">
            <wml2:processing>
                <xsl:attribute name="xlink:href">
                    <!-- this is a WaterML 1 definition (or odm definition) -->
                    <xsl:text>#</xsl:text>
                    <xsl:call-template name="QualityControlIdentifier">
                        <xsl:with-param name="qc" select="wml:qualityControlLevel[1]/wml:qualityControlLevelCode"></xsl:with-param>
                    </xsl:call-template>
                    
                </xsl:attribute>

                <xsl:attribute name="xlink:title">
                    <xsl:value-of select="wml:qualityControlLevel[1]/wml:definition"/>
                </xsl:attribute>
            </wml2:processing>
        </xsl:if>
        
        <xsl:if test="count(wml:source) = 1 ">
            
            <wml2:source>
                <xsl:attribute name="xlink:href">
                    <xsl:value-of select="concat('#',generate-id( wml:source/wml:sourceCode ) )"/>
                </xsl:attribute>
            </wml2:source>
            
        </xsl:if>
        <xsl:if test="$comments = 'true' ">  
        <xsl:comment>8.6.3 unitOfMeasure. Mapping. only one or two
                                            are done presently. The unit of measure is specified
                                            using the ISO19103 UnitOfMeasure type. </xsl:comment>
      </xsl:if>
        <wml2:uom>
            <xsl:attribute name="code">
                <xsl:call-template name="UOMCreator">
                    <xsl:with-param name="Unit" select="../wml:variable/wml:unit"/>
                </xsl:call-template>

            </xsl:attribute>
        </wml2:uom>
        <xsl:if test="$comments = 'true' ">
            <xsl:comment>8.6.5 Data type mapping to
                                            InterpolationType</xsl:comment>
       </xsl:if>
        <xsl:call-template name="DataTypeToInterpolationType">
            <xsl:with-param name="dataTypeName" select="../wml:variable/wml:dataType"/>
        </xsl:call-template>
        
        <xsl:if test="../wml:variable/wml:timeScale/wml:timeSupport > 0">
            <wml2:aggregationDuration>
                <xsl:call-template name="TimeUnitToPeriod">
                    <xsl:with-param name="TimeSupport"
                        select="../wml:variable/wml:timeScale/wml:timeSupport"/>
                    <xsl:with-param name="Unit" select="../wml:variable/wml:timeScale/wml:unit"
                    />
                </xsl:call-template>
            </wml2:aggregationDuration>
        </xsl:if>
        
        <!--      <wml2:interpolationType>

        <xsl:attribute name="xlink:href">
                <xsl:value-of
                    select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',../wml:variable/wml:dataType)"
                />
            </xsl:attribute>
            <xsl:attribute name="xlink:title">
                <xsl:value-of select="../wml:variable/wml:dataType"/>
            </xsl:attribute>
        </wml2:interpolationType>

</wml2:interpolationType>-->


        <!--          <xsl:if test=" count(wml:censorCode) = 1 ">
                                            <wml2:censoredReason>
                                                <xsl:attribute name="xlink:href">
                                                  <xsl:value-of
                                                  select="concat('#censorCode-',translate(wml:censorCode[1]/wml:censorCode, &quot; &quot;, &quot;_&quot;))"
                                                  />
                                                </xsl:attribute>
                                            </wml2:censoredReason>
                                        </xsl:if>
                                        -->


    </xsl:template>

    <xsl:template name="TVPMetadata">
        <xsl:choose>
            <xsl:when test="count(../wml:censorCode) > 1 and @censorCode">
                <xsl:call-template name="mapCensorCode">
                    <xsl:with-param name="censorCode" select="@censorCode"/>
                </xsl:call-template>
            </xsl:when>
            <!-- do not want to assume good -->
            <!--   <xsl:when  test="count(../wml:censorCode) > 1 and not( @censorCode)">
                <xsl:call-template name="QualityElement">
                    <xsl:with-param name="href">http://www.opengis.net/def/waterml/2.0/quality/good </xsl:with-param>
                    <xsl:with-param name="title">Good</xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            -->
            <xsl:otherwise/>
        </xsl:choose>
        <xsl:if test="@labSampleCode">
            <xsl:variable name="sampleCode" select="@labSampleCode"/>
            <xsl:comment>link not functional.
                                                  relatedObservation for sample <xsl:value-of select="$sampleCode"/>
                                                  </xsl:comment>

            <xsl:call-template name="sampleToRelatedObservation">
                <xsl:with-param name="sample"
                    select="../wml:sample[wml:labSampleCode = $sampleCode][1]"/>
            </xsl:call-template>

        </xsl:if>
        <xsl:if test="@offsetValue">
            <xsl:variable name="offsetType" select="@offsetTypeCode"/>
            <wml2:qualifier>

                <swe:Quantity>
                    <xsl:attribute name="definition">
                        <xsl:text>http://hiscentral.cuahsi.org/wml/offsetValue</xsl:text>
                    </xsl:attribute>
                    <swe:identifier><xsl:value-of select="concat('offsetTypeCode-',@offsetTypeCode)"/></swe:identifier>
                    <swe:uom>
                        <xsl:attribute name="code">
                            <xsl:value-of
                                select="../wml:offset[wml:offsetTypeCode/text()=$offsetType]/wml:unit/wml:unitAbbreviation"
                            />
                        </xsl:attribute>
                    </swe:uom>
                    <swe:value>
                        <xsl:value-of select="@offsetValue"/>
                    </swe:value>
                </swe:Quantity>
            </wml2:qualifier>


        </xsl:if>
        <!-- what to do with method? -->
        <xsl:if test=" count(../wml:method) > 1 and @methodCode">
            <wml2:qualifier>
  <!--              <xsl:attribute name="xlink:href">
                    <xsl:text>#</xsl:text>
                    <xsl:text>methodCode-</xsl:text>
                    <xsl:call-template name="MethodIdentifier">
                        <xsl:with-param name="method" select="wml:method"/>
                    </xsl:call-template>
                </xsl:attribute>
                <xsl:attribute name="xlink:role">
                    <xsl:text>http://hiscentral.cuahsi.org/wml/qualifier/method</xsl:text>
                </xsl:attribute>
                -->
                <xsl:call-template name="sweText">
                    <xsl:with-param name="definitionUrl"><xsl:text>#</xsl:text>
                        <xsl:text>methodCode-</xsl:text>
                        <xsl:call-template name="MethodIdentifier">
                            <xsl:with-param name="method" select="wml:method"/> 
                        </xsl:call-template></xsl:with-param>
                <xsl:with-param name="value" select="wml:method/wml:methodDescription"></xsl:with-param>
                </xsl:call-template>
            </wml2:qualifier>
        </xsl:if>
        <xsl:if test=" count(../wml:qualifier) > 1 and @qualifiers">
            <!-- no simple way to split a string in xslt v1. 
                                                           http://stackoverflow.com/questions/584082/xslt-best-way-to-split-and-render-comma-separated-text-as-html
                                                       space delimited multiple qualifiers are not going to link correctly
               
            -->
            <wml2:qualifier>
           <!--     <xsl:attribute name="xlink:href">
                    <xsl:text>#</xsl:text>
                    <xsl:call-template name="QualifierIdentifier">
                        <xsl:with-param name="qualifier" select="@qualifiers"></xsl:with-param>
                    </xsl:call-template>

                </xsl:attribute>
                <xsl:attribute name="xlink:role">
                    <xsl:text>http://www.opengis.net/def/qualifiertype/waterml2/generic</xsl:text>

                </xsl:attribute>
                -->
                <xsl:call-template name="sweText">
                    <xsl:with-param name="definitionUrl"><xsl:text>#</xsl:text>
                        <xsl:call-template name="QualifierIdentifier">
                            <xsl:with-param name="qualifier" select="@qualifiers"></xsl:with-param>
                        </xsl:call-template></xsl:with-param>
                    <xsl:with-param name="value" select="@qualifiers"></xsl:with-param>
                </xsl:call-template>
            </wml2:qualifier>
        </xsl:if>
        <xsl:if test="count(../wml:qualityControlLevel) > 1 and @qualityControlLevelCode">
            <wml2:processing>
                <xsl:attribute name="xlink:href">
                    <xsl:text>#</xsl:text>
                    <xsl:call-template name="QualityControlIdentifier">
                        <xsl:with-param name="qc" select="@qualityControlLevelCode"></xsl:with-param>
                    </xsl:call-template>
  
                </xsl:attribute>
            </wml2:processing>
        </xsl:if>
        
        <xsl:if test="count(../wml:source) > 1 and @sourceCode">
            <xsl:variable name="sourceCode" select="@sourceCode"/>
                    <wml2:source>
                        <xsl:attribute name="xlink:href">
                            <xsl:value-of select="concat('#',generate-id( ../wml:source/wml:sourceCode[text() =$sourceCode] ) )"/>
                        </xsl:attribute>
                    </wml2:source>
            
        </xsl:if>
        
        <xsl:if test="count(../wml:censorCode) > 1 and @censorCode">
            <xsl:choose>
                <xsl:when test="@censorCode = 'nc'"/>
                <xsl:otherwise>
                    <wml2:censoredReason>
                        <xsl:attribute name="xlink:href">
                            <xsl:value-of select="concat('#censorCode-',@censorCode)"/>
                        </xsl:attribute>
                    </wml2:censoredReason>
                </xsl:otherwise>
            </xsl:choose>

        </xsl:if>
        



    </xsl:template>

 <xsl:template name="sweQuantity">
     <xsl:param name="definitionUrl"></xsl:param>
     <xsl:param name="uom"></xsl:param>
     <xsl:param name="value"></xsl:param>
     <swe:Quantity definition="#qualifier_v_offset">
		 <xsl:attribute name="definition">
			 <xsl:value-of
						select="$definitionUrl"/>
		 </xsl:attribute>
         <swe:uom code="m">
             <xsl:attribute name="code">
				 <xsl:value-of select="$uom"/>
				 </xsl:attribute>
			 
         </swe:uom>
         <swe:value><xsl:value-of select="$value"></xsl:value-of></swe:value>
     </swe:Quantity>
 </xsl:template>


    <xsl:template name="sweTextNoValue">
        <xsl:param name="definitionUrl"></xsl:param>       
        <swe:Text definition="#qualifier-A">
			<xsl:attribute name="definition">
				<xsl:value-of select="$definitionUrl"/>
			</xsl:attribute>
         </swe:Text>     
    </xsl:template>
    
    <xsl:template name="sweText">
        <xsl:param name="definitionUrl"/>       
        <xsl:param name="value"></xsl:param>
        <swe:Text definition="#qualifier-A">
            <xsl:attribute name="definition" ><xsl:value-of select="$definitionUrl"/></xsl:attribute>
            <swe:value><xsl:value-of select="$value"></xsl:value-of></swe:value>
        </swe:Text>     
    </xsl:template>
    
    <xsl:template name="sweCategory">
        <xsl:param name="definitionUrl"></xsl:param>  
        <xsl:param name="codeSpaceUrl"/> 
        <xsl:param name="codeSpaceTitle"></xsl:param> 
        <xsl:param name="description" /> 
        <xsl:param name="value"></xsl:param> 
        <swe:Category >
			<xsl:attribute name="definition">
				<xsl:value-of select="$definitionUrl"/>
			</xsl:attribute>
             <xsl:if test="$description">
            <swe:description><xsl:value-of select="$value"/></swe:description>
            </xsl:if>
            <xsl:if test="$codeSpaceUrl">
            <swe:codeSpace xlink:href="http://www.bom.gov.au/info/wwords/" xlink:title="BoM weather words"/>
				<xsl:attribute name="xlink:href">
					<xsl:value-of select="$codeSpaceUrl"/>
				</xsl:attribute>
				<xsl:attribute name="xlink:title">
					<xsl:value-of select="$codeSpaceTitle"/>
				</xsl:attribute>
            </xsl:if>
           <swe:value><xsl:value-of select="$value"></xsl:value-of></swe:value>
       </swe:Category>   
    </xsl:template>
    
    <xsl:template name="sampleToRelatedObservation" match="wml:sample">
        <xsl:param name="sample"/>

        <!--  <sample sampleID="9738">
        <labSampleCode>CEAP052005-PAR-TSS</labSampleCode>
        <sampleType>Grab</sampleType>
        <labMethod>
        <labCode>CEAP052005-PAR-TSS</labCode>
        <labName>USU Analytical Laboratory</labName>
        <labOrganization>Utah State University</labOrganization>
        <labMethodName>EPA 340.2</labMethodName>
        <labMethodDescription>Total Suspended Solids, Mass Balance</labMethodDescription>
        </labMethod>
        </sample>
         -->
        <wml2:relatedObservation>
            <om:ObservationContext>
                <om:role>
                    <xsl:attribute name="xlink:href"
                        >http://www.opengis.net/def/relatedObservation/WaterML/2.0/analyticalSample</xsl:attribute>
                    <xsl:attribute name="xlink:title">Analytical Sample Observation</xsl:attribute>
                </om:role>
                <om:relatedObservation>
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of select="concat($wqxBase,$sample/wml:labSampleCode)"/>
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title">
                        <xsl:value-of select="concat('LabCode:',$sample/wml:labSampleCode)"/>
                        <xsl:if test="sampleType">
                            <xsl:value-of select="concat(' SampleType:',$sample/wml:sampleType)"/>
                        </xsl:if>
                        <xsl:if test="labMethod/labMethodName">
                            <xsl:value-of
                                select="concat(' Lab Method:',$sample/wml:labMethod/wml:labMethodName)"
                            />
                        </xsl:if>

                    </xsl:attribute>
                </om:relatedObservation>
            </om:ObservationContext>

        </wml2:relatedObservation>
    </xsl:template>
    <!--   <xsl:include href="WaterML1_1_common_to_waterml2.xsl"/> -->
</xsl:stylesheet>
