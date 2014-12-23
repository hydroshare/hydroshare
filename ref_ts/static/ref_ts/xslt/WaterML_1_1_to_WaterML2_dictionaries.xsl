<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xd="http://www.oxygenxml.com/ns/doc/xsl"
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
    xmlns:gss="http://www.isotc211.org/2005/gss" version="2.0"
    xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
    exclude-result-prefixes="xs xd"
    >
    <!-- exclude-result-prefixes="xs" -->
    <!-- need to import because this also has a wml:timeSeriesResponse template -->
    <xsl:import href="WaterML1_1_timseries_WaterProcess_to_WaterML2.xsl"/>
    <xsl:import href="WaterML1_1_timseries_ObservedProperty_to_WaterML2.xsl"/>
    <xsl:import href="WaterML_1_1_source_to_waterML2_identification.xsl"/>
    <xsl:import href="WaterML1_1_site_to_WaterML2.xsl"/>
    <xsl:import href="WaterML1_1_common_to_waterml2.xsl"/>
    
    <xd:doc scope="stylesheet">
        <xd:desc>
            <xd:p><xd:b>Created on:</xd:b> Feb 23, 2012</xd:p>
            <xd:p><xd:b>Author:</xd:b> valentin</xd:p>
            <xd:p></xd:p>
        </xd:desc>
    </xd:doc>
    <xsl:template name="localDictVaraible" match="wml:timeSeries/wml:variable">
        
   
        <xsl:if test="count(wml:timeSeries/wml:variable) >0">
        <wml2:localDictionary>
            <gml:Dictionary gml:id="phenomena">
                <gml:identifier
                    codeSpace="http://hiscentral.cuahsi.org/waterml2/dictionaries/"
                    >phenomena</gml:identifier>
                <!--    <xsl:for-each select="wml:timeSeries/wml:variable">
                      -->
                <xsl:for-each
                    select="//wml:timeSeries/wml:variable[generate-id(.) =
                    generate-id(key('variables',  wml:variableCode)[1])]">
                    <!-- <gml:phenomenonEntry>
                                <gml:Definition>
                                    <xsl:attribute name="gml:id">
                                        <xsl:value-of select="concat('qualifier-',translate( wml:variableCode[1], &quot; &quot;, &quot;_&quot;))" />
                                    </xsl:attribute>
                                    <gml:identifier>
                                        <xsl:attribute name="codeSpace">wml:variableCode[1][@network]</xsl:attribute>
                                        <xsl:value-of select="wml:variableCode[1][text()]" />
                                    </gml:identifier>
                                    <gml:name>
                                        <xsl:attribute name="codeSpace">wml:variableCode[1][@network]</xsl:attribute>
                                        <xsl:value-of select="wml:variableName[text()]" />
                                    </gml:name>
                                    
                                </gml:Definition>
                            </gml:phenomenonEntry>
                           -->
                    <xsl:call-template name="VariablePhenomenaDictionaryEntry">
                        <xsl:with-param name="observedPropertiesBase">
                   <!--         <xsl:value-of select="$observedPropertiesBase"/> -->
                        </xsl:with-param> 
                        <!--     <xsl:with-param name="concept">
                                    <xsl:value-of select="$concept"/>
                                </xsl:with-param>
                                -->
                        <xsl:with-param name="concept">
                            <xsl:call-template name="HisOntologyMapper">
                                <xsl:with-param name="VariableCode" select="concat(wml:variableCode[1]/@vocabulary,':', wml:variableCode)"></xsl:with-param>
                            </xsl:call-template>
                        </xsl:with-param>
                    </xsl:call-template>
                </xsl:for-each>
                <!--  <xsl:variable name="PhenomenonEntry"> <xsl:call-template name="phenomenonEntry" >
                            <xsl:with-param name="wfsBase"><xsl:value-of select="$wfsBase"/></xsl:with-param> 
                            <xsl:with-param name="observedPropertiesBase"><xsl:value-of select="observedPropertiesBase"/></xsl:with-param>
                            <xsl:with-param name="concept"><xsl:value-of select="$concept"/></xsl:with-param>
                        </xsl:call-template></xsl:variable>
                        <xsl:comment> 
                           <xsl:value-of select="$PhenomenonEntry" disable-output-escaping="no"></xsl:value-of>
                        </xsl:comment>
                        -->
            </gml:Dictionary>
        </wml2:localDictionary>
    </xsl:if>
    </xsl:template>
    <xsl:template name="localDictQualifier" match="wml:timeSeries/wml:values/wml:qualifier">
    <!--      <xsl:if test="count(distinct-values(wml:timeSeries/wml:values/wml:qualifier)) >0"> -->
    <!-- xslt 2.0 -->
    <!-- <xsl:if test="count(wml:timeSeries/wml:values/wml:qualifier[not(qualifierCode = preceding::qualifierCode)]) >0">
            -->
    <xsl:if test="count(wml:timeSeries/wml:values/wml:qualifier) >0">
        <wml2:localDictionary>
            <gml:Dictionary gml:id="qualifier">
                <gml:identifier
                    codeSpace="http://hiscentral.cuahsi.org//waterml2/dictionaries/"
                    >qualifier</gml:identifier>
                <xsl:for-each
                    select="//wml:timeSeries/wml:values/wml:qualifier[generate-id(.) =
                    generate-id(key('qualifiers',  wml:qualifierCode)[1])]">
                    
                    <!--     <xsl:for-each select="wml:timeSeries/wml:values/wml:qualifier[not(qualifierCode = preceding::qualifierCode)]">
                   -->
                    <!-- this will replace *** with ttt... 
                        '***','tna' => 'ttt'
                        -->        
                    <xsl:variable name="qualifierCode" select="translate(wml:qualifierCode, '*', 't')" ></xsl:variable> 
                    <gml:dictionaryEntry>
                        <gml:Definition>
                            <xsl:attribute name="gml:id">
                                
                                <xsl:call-template name="QualifierIdentifier">
                                    <xsl:with-param name="qualifier" select="$qualifierCode"></xsl:with-param>
                                </xsl:call-template>
                                
                            </xsl:attribute>
                            <gml:identifier>
                                <xsl:attribute name="codeSpace"
                                    >http://hiscentral.cuahsi.org/wml/qualifierCode</xsl:attribute>
                                <xsl:value-of select="$qualifierCode"/>
                            </gml:identifier>
                            <gml:name>
                                <xsl:attribute name="codeSpace"
                                    >http://hiscentral.cuahsi.org/wml/qualifierCode</xsl:attribute>
                                <xsl:value-of select="wml:qualifierDescription"/>
                            </gml:name>
                            
                        </gml:Definition>
                    </gml:dictionaryEntry>
                </xsl:for-each>
            </gml:Dictionary>
        </wml2:localDictionary>
    </xsl:if>
</xsl:template>
    
    <xsl:template name="localDictQCLevel" match="wml:timeSeries/wml:values/wml:qualityControlLevel">
        <!--  <xsl:if test="not(empty($unique-list))"> -->
        <xsl:if test="count(wml:timeSeries/wml:values/wml:qualityControlLevel) >0">
            
            <!-- works in xslt 2.0 aka not .net -->
            <!--  <xsl:if test="count(//wml:timeSeries/wml:values/wml:qualityControlLevel[not(qualityControlLevelCode = preceding::qualityControlLevelCode)]  )>0">
          -->
            <wml2:localDictionary>
                <gml:Dictionary gml:id="quality">
                    <gml:identifier codeSpace="http://www.cuahsi.org/waterml2/dictionaries/"
                        >quality</gml:identifier>
                    <!--  <xsl:for-each select="wml:timeSeries/wml:values/wml:qualityControlLevel"> -->
                    <!-- xslt 2.0 -->
                    <!-- <xsl:for-each select="//wml:timeSeries/wml:values/wml:qualityControlLevel[not(qualityControlLevelCode = preceding::qualityControlLevelCode)] ">
                        -->
                    <xsl:for-each
                        select="//wml:timeSeries/wml:values/wml:qualityControlLevel[generate-id(.) =
                        generate-id(key('qclevel',  wml:qualityControlLevelCode)[1])] ">
                        <!--key('qclevel', '0' )  wml:qualityControlLevelCode -->
                        <gml:dictionaryEntry>
                            <gml:Definition>
                                <xsl:attribute name="gml:id">
                                    <xsl:call-template name="QualityControlIdentifier">
                                        <xsl:with-param name="qc" select="wml:qualityControlLevelCode"></xsl:with-param>
                                    </xsl:call-template>
                                    
                                </xsl:attribute>
                                <gml:identifier>
                                    <xsl:attribute name="codeSpace"
                                        >http://hiscentral.cuahsi.org/wml/qualityControlLevelCode</xsl:attribute>
                                    <xsl:value-of select="wml:qualityControlLevelCode"/>
                                </gml:identifier>
                                <gml:name>
                                    <xsl:attribute name="codeSpace"
                                        >http://hiscentral.cuahsi.org/wml/qualityControlLevelCode</xsl:attribute>
                                    <xsl:value-of select="wml:definition"/>
                                </gml:name>
                                <gml:remarks>
                                    <xsl:value-of select="wml:explanation"/>
                                </gml:remarks>
                            </gml:Definition>
                        </gml:dictionaryEntry>
                    </xsl:for-each>
                </gml:Dictionary>
            </wml2:localDictionary>
        </xsl:if>
    </xsl:template>
    
    <xsl:template name="localDictCensorCode" match="wml:timeSeries/wml:values/wml:censorCode">
        <xsl:if test="count(//wml:timeSeries/wml:values/wml:censorCode) >0">
            <wml2:localDictionary>
                <gml:Dictionary gml:id="censorCode">
                    <xsl:if test="$comments = 'true' ">
                        <xsl:comment>8.6.4 Data quality. Mapping needed</xsl:comment>
                   </xsl:if>
                    <gml:identifier codeSpace="http://www.cuahsi.org/waterml2/dictionaries/"
                        >censorCode</gml:identifier>
                    <xsl:for-each
                        select="//wml:timeSeries/wml:values/wml:censorCode[generate-id(.) =
                        generate-id(key('censorCode',  wml:censorCode)[1])] ">
                        <gml:dictionaryEntry>
                            <gml:Definition>
                                <xsl:attribute name="gml:id">
                                    <xsl:value-of select="concat('censorCode-',wml:censorCode)"
                                    />
                                </xsl:attribute>
                                <gml:identifier>
                                    <xsl:attribute name="codeSpace"
                                        >http://hiscentral.cuahsi.org/wml/censored</xsl:attribute>
                                    <xsl:value-of select="wml:censorCode"/>
                                </gml:identifier>
                                <gml:name>
                                    <xsl:attribute name="codeSpace"
                                        >http://hiscentral.cuahsi.org/wml/censored</xsl:attribute>
                                    <xsl:value-of select="wml:censorCodeDescription"/>
                                </gml:name>
                            </gml:Definition>
                        </gml:dictionaryEntry>
                    </xsl:for-each>
                </gml:Dictionary>
            </wml2:localDictionary>
        </xsl:if>
    </xsl:template>
    <xsl:template name="localDictMethod" match="wml:timeSeries/wml:values/wml:method">
        <xsl:if test="count(//wml:timeSeries/wml:values/wml:method) >0">
            <wml2:localDictionary>
                <gml:Dictionary gml:id="method">
                    <gml:identifier codeSpace="http://www.cuahsi.org/waterml2/dictionaries/"
                        >method</gml:identifier>
                    <xsl:choose>
                        <xsl:when
                            test="count(//wml:timeSeries/wml:values/wml:method[generate-id(.) =
                            generate-id(key('methodCode',  wml:methodCode)[1])]) >0">
                            <xsl:variable name="methods"
                                select="//wml:timeSeries/wml:values/wml:method[generate-id(.) =
                                generate-id(key('methodCode',  wml:methodCode)[1])] "/>
                            <xsl:call-template name="MethodDictionary">
                                <xsl:with-param name="methods" select="$methods"/>
                            </xsl:call-template>
                        </xsl:when>
                        <xsl:otherwise>
                            <xsl:variable name="methods"
                                select="//wml:timeSeries/wml:values/wml:method[generate-id(.) =
                                generate-id(key('methodID',  @methodID)[1])] "/>
                            <xsl:call-template name="MethodDictionary">
                                <xsl:with-param name="methods" select="$methods"/>
                            </xsl:call-template>
                        </xsl:otherwise>
                        
                    </xsl:choose>
                    
                </gml:Dictionary>
            </wml2:localDictionary>
        </xsl:if>
    </xsl:template>
    <xsl:template name="MethodDictionary">
        <xsl:param name="methods"/>
        <xsl:for-each select="$methods">
            <gml:dictionaryEntry>
                <gml:Definition>
                    <xsl:attribute name="gml:id">
                        <xsl:text>methodCode-</xsl:text>
                        <xsl:call-template name="MethodIdentifier">
                            <xsl:with-param name="method" select="."/>
                        </xsl:call-template>
                    </xsl:attribute>
                    <xsl:if test="wml:method/wml:MethodLink">
                        <gml:descriptionReference>
                            <xsl:attribute name="xlink:href">
                                <xsl:value-of select="./wml:MethodLink"/>
                            </xsl:attribute>
                        </gml:descriptionReference>
                    </xsl:if>
                    <gml:identifier>
                        <xsl:attribute name="codeSpace"
                            >http://hiscentral.cuahsi.org/wml/method</xsl:attribute>
                        <xsl:call-template name="MethodIdentifier">
                            <xsl:with-param name="method" select="."/>
                        </xsl:call-template>
                    </gml:identifier>
                    <gml:name>
                        <xsl:attribute name="codeSpace"
                            >http://hiscentral.cuahsi.org/wml/method</xsl:attribute>
                        <xsl:value-of select="./wml:methodDescription"/>
                    </gml:name>
                </gml:Definition>
            </gml:dictionaryEntry>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="localDictOffset" match="wml:timeSeries/wml:values/wml:offset">
        <xsl:if test="count(//wml:timeSeries/wml:values/wml:offset) >0">
            <wml2:localDictionary>
                <gml:Dictionary gml:id="offset">
                    
                    <gml:identifier codeSpace="http://www.cuahsi.org/waterml2/dictionaries/"
                        >censorCode</gml:identifier>
                    <xsl:for-each
                        select="//wml:timeSeries/wml:values/wml:offset[generate-id(.) =
                        generate-id(key('offset',  wml:offsetTypeCode)[1])] ">
                        <gml:dictionaryEntry>
                            <gml:DefinitionCollection aggregationType="set" gml:id="">
                                <xsl:attribute name="gml:id">
                                    <xsl:value-of
                                        select="concat('offsetType-',wml:offsetTypeCode)"/>
                                </xsl:attribute>
                                <gml:identifier codeSpace="http://hiscentral.cuahsi.org/wml/offset"><xsl:value-of
                                    select="concat( 'offsetType-', wml:offsetTypeCode )"/></gml:identifier>
                                <gml:dictionaryEntry>
                                    <gml:Definition>
                                        <xsl:attribute name="gml:id">
                                            <xsl:value-of
                                                select="concat('offsetTypeDescripton-',wml:offsetTypeCode)"
                                            />
                                        </xsl:attribute>
                                        <gml:identifier>
                                            <xsl:attribute name="codeSpace"
                                                >http://hiscentral.cuahsi.org/wml/offset</xsl:attribute>
                                            <xsl:value-of select="wml:offsetTypeCode"/>
                                        </gml:identifier>
                                        <gml:name>
                                            <xsl:attribute name="codeSpace"
                                                >http://hiscentral.cuahsi.org/wml/offset</xsl:attribute>
                                            <xsl:value-of select="wml:offsetDescription"/>
                                        </gml:name>
                                    </gml:Definition>
                                </gml:dictionaryEntry>
                                <gml:dictionaryEntry>
                                    <gml:UnitDefinition gml:id="">
                                        <xsl:attribute name="gml:id">
                                            <xsl:value-of
                                                select="concat('offsetTypeUnits-',wml:offsetTypeCode)"
                                            />
                                        </xsl:attribute>
                                        <gml:identifier>
                                            <xsl:attribute name="codeSpace"
                                                >http://www.opengis.net/def/uom/UCUM/0</xsl:attribute>
                                            <!--  <xsl:text>unit of measure</xsl:text> -->
                                        </gml:identifier>
                                        <gml:name>
                                            <xsl:attribute name="codeSpace"
                                                >http://hiscentral.cuahsi.org/wml/units</xsl:attribute>
                                            <xsl:call-template name="UOMCreator">
                                                <xsl:with-param name="Unit" select="wml:unit"/>
                                            </xsl:call-template>
                                        </gml:name>
                                    </gml:UnitDefinition>
                                </gml:dictionaryEntry>
                            </gml:DefinitionCollection>
                        </gml:dictionaryEntry>
                        
                    </xsl:for-each>
                </gml:Dictionary>
            </wml2:localDictionary>
        </xsl:if>
    </xsl:template>
</xsl:stylesheet>