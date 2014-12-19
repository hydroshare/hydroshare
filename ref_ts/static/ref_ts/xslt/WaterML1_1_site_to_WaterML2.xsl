<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:wml2="http://www.opengis.net/waterml/2.0"
    xmlns:sam="http://www.opengis.net/sampling/2.0"
    xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:om="http://www.opengis.net/om/2.0" 
    xmlns:sams="http://www.opengis.net/samplingSpatial/2.0"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:wml="http://www.cuahsi.org/waterML/1.1/"
    xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
    exclude-result-prefixes="xs"
    version="1.0">
    
    <xsl:import href="WaterML1_1_common_to_waterml2.xsl" />
  
    
    <xsl:template name="SiteInfoToWaterObservationPoint">
        <xsl:param name="sourceInfoType"></xsl:param>
        <wml2:MonitoringPoint >
            <xsl:attribute name="gml:id">
                <xsl:call-template name="SiteIdentifier">
                    <xsl:with-param name="site" select="$sourceInfoType"></xsl:with-param>
                </xsl:call-template>
          
                <!-- <xsl:value-of select="$sourceInfoType/wml:siteCode" /> -->
            </xsl:attribute>
            
            <gml:identifier >
                <xsl:attribute name="codeSpace">http://hiscentral.cuahsi.org/network/<xsl:value-of select="$sourceInfoType/wml:siteCode/@network"/></xsl:attribute>
                <xsl:value-of select="$sourceInfoType/wml:siteCode"/>
            </gml:identifier>
            <gml:name>
                <xsl:value-of select="$sourceInfoType/wml:siteName"/>
            </gml:name>
            <xsl:if test="$comments = 'true'">
                <xsl:comment>We know the sampling point, but do not the actual physical "sampled feature"; eg which river,  stream, lake. </xsl:comment>   
                <xsl:comment>as per https://www.seegrid.csiro.au/wiki/AppSchemas/ObservationsAndSampling#Unknown_features
       </xsl:comment>
            </xsl:if>
            <sam:sampledFeature xlink:title="Unsepecified Sampled Feature" xlink:role="http://hiscentral.cuahsi.org/wml/site" xlink:href="urn:ogc:def:nil:OGC:unknown"/> 
            
            <xsl:apply-templates select="$sourceInfoType/wml:elevation_m" />  
            
            
            <xsl:for-each select="$sourceInfoType/wml:note">
                <sam:parameter>
                    <om:NamedValue>
                        <om:name >
                            <xsl:attribute name="xlink:href">
                                <xsl:value-of select='concat("http://hiscentral.cuahsi.org/wml/siteProperty/", @title)'/>
                            </xsl:attribute>
                            <xsl:attribute name="xlink:title">
                                <xsl:value-of select='@title'/>
                            </xsl:attribute>
                        </om:name>
                        <om:value xsi:type="xsd:string">
                            <xsl:value-of select="."/>
                        </om:value>
                    </om:NamedValue>
                </sam:parameter>
            </xsl:for-each>
            
            <xsl:for-each select="$sourceInfoType/wml:siteProperty">
                <sam:parameter>
                    <om:NamedValue>
                        <om:name >
                            <xsl:attribute name="xlink:href">
                                <xsl:value-of select='concat("http://hiscentral.cuahsi.org/wml/siteProperty/", translate(@name," ","_"  ) )'/>
                            </xsl:attribute>
                            <xsl:attribute name="xlink:title">
                                <xsl:value-of select='@name'/>
                            </xsl:attribute>
                        </om:name>
                        <om:value xsi:type="xsd:string">
                            <xsl:value-of select="."/>
                        </om:value>
                    </om:NamedValue>
                </sam:parameter>
            </xsl:for-each>
            
            <sams:shape>
                <gml:Point> 
                    <xsl:attribute name="gml:id">
                       <xsl:call-template name="SiteIdentifier">
                            <xsl:with-param name="site" select="$sourceInfoType"></xsl:with-param>
                        </xsl:call-template>
                     
                        <xsl:text>_pos</xsl:text>
                    </xsl:attribute>
                    <gml:pos>
                        <xsl:attribute name="srsName">
                            <xsl:value-of select="$sourceInfoType/wml:geoLocation/wml:geogLocation/@srs"/>
                        </xsl:attribute>
                        <xsl:value-of select="$sourceInfoType/wml:geoLocation/wml:geogLocation/wml:latitude"/> 
                        <xsl:text> </xsl:text><xsl:value-of select="$sourceInfoType/wml:geoLocation/wml:geogLocation/wml:longitude"/>
                    </gml:pos>
                </gml:Point>
            </sams:shape>
            <wml2:monitoringType xlink:href="http://www.cuahsi.org/waterml2/siteType/surfaceWater" xlink:title="Surface Water"/>
            <xsl:if test="$comments = 'true' ">
                <xsl:comment> wml2 descriptionReference pointer to a web page </xsl:comment>
            </xsl:if>
            <!--   <wml2:descriptionReference xlink:href="http://kiwis.kisters.de/datasource/0/stations/6731310" xlink:title="DOVIKFOSS"/>
          -->
            <!--					<wml2:gaugeDatum></wml2:gaugeDatum>
       -->
            <xsl:apply-templates select="$sourceInfoType/wml:timeZoneInfo" />
            <xsl:apply-templates select="$sourceInfoType/wml:verticalDatum" />  
        </wml2:MonitoringPoint>
    </xsl:template> 
    
    <xsl:template   match="wml:timeZoneInfo" name="TimeZone">
        
        <wml2:timeZone>
            <wml2:TimeZone>
                <wml2:zoneOffset><xsl:value-of select="wml:defaultTimeZone/@zoneOffset"></xsl:value-of></wml2:zoneOffset>
                <wml2:zoneAbbreviation><xsl:value-of select="wml:defaultTimeZone/@zoneAbbreviation"/></wml2:zoneAbbreviation>
                
            </wml2:TimeZone>
        </wml2:timeZone>
    </xsl:template>
    
    <xsl:template match="wml:elevation_m">
        <!--  <sam:parameter>
                <om:NamedValue>
                  <om:name xlink:href="http://hiscentral.cuahsi.org/wml/siteProperty/elevation_m/" xlink:title="elevation in meters">
                  </om:name>
                  <om:value xsi:type="gml:MeasureType" uom="m"><xsl:value-of select="."/></om:value> 
                </om:NamedValue>
              </sam:parameter>
              -->
        <sam:parameter>
            <om:NamedValue>
                <om:name xlink:href="http://hiscentral.cuahsi.org/wml/siteProperty/elevation_m/" xlink:title="elevation in meters">
                </om:name>
                <om:value xsi:type="xsd:string" ><xsl:value-of select="."/>m</om:value> 
            </om:NamedValue>
        </sam:parameter>
    </xsl:template>
    
    <xsl:template match="wml:verticalDatum">
        <!--   <sam:parameter>
                <om:NamedValue>
                  <om:name xlink:href="http://hiscentral.cuahsi.org/wml/siteProperty/verticalDatum/" xlink:title="Vertical Datum">
                  </om:name>
                  <om:value xsi:type="xsd:string">
                    <xsl:value-of select="."/>
                  </om:value>
                </om:NamedValue>
              </sam:parameter>
              -->
        <wml2:verticalDatum>
            <xsl:attribute name="xlink:href">
                <xsl:call-template name="verticalDataumMapper">
                    <xsl:with-param name="verticalDataum"><xsl:value-of select="."/></xsl:with-param>
                </xsl:call-template>
               
            </xsl:attribute>
            <xsl:attribute name="xlink:title"><xsl:value-of select="."/></xsl:attribute>
        </wml2:verticalDatum>
    </xsl:template> 
</xsl:stylesheet>