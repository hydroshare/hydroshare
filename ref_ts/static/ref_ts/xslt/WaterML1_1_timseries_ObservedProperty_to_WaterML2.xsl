<?xml version="1.0" encoding="UTF-8"?>
<!-- Created with Liquid XML Studio Developer Edition (Education) 9.0.11.3078 (http://www.liquid-technologies.com) -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xmlns:wml2="http://www.opengis.net/waterml/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
  xmlns:om="http://www.opengis.net/om/2.0" xmlns:xlink="http://www.w3.org/1999/xlink"
  xmlns:wml="http://www.cuahsi.org/waterML/1.1/" xmlns:fn="http://www.w3.org/2005/xpath-functions"
  xmlns:swe="http://www.opengis.net/swe/2.0"
  xmlns:op="http://schemas.opengis.net/op"
  xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
  xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs" version="2.0">
  <!--
    <element name="observedProperty" type="gml:ReferenceType">
<annotation>
<documentation>	The association Phenomenon shall link the OM_Observation to the
GFI_PropertyType (C.2.2) for which the OM_Observation:result (6.2.2.9)
provides an estimate of its value. The property type has the role
observedProperty with respect to the observation. The observed property
shall be a phenomenon associated with the type of the featureOfInterest.
NOTE An observed property may, but need not be modelled as a property (in	
the sense of the General Feature Model) in a formal application schema that
defines the type of the feature of interest The observed property supports
semantic or thematic classification of observations, which is useful for	
discovery and data fusion. 
If provided using another encoding (e.g. OWL or SWEET) 
then the description must be in a remote repository and xlink reference used.
</documentation>
</annotation>
</element>
    -->
  <!--
swe:Phenomenon

Use the generic gml:DefinitionType for basic Phenomenon definitions,
gml:description may be used for a more extensive description of the semantics, 
with a link to a definitive
version (if available).
gml:name should be used for the "short name" or label.

<swe:Phenomenon gml:id="ID">
   <gml:metaDataProperty>
      
</gml:metaDataProperty>
<gml:description xlink-attrs >string</gml:description>
<gml:name codespace="">string</gml:name>
</swe:Phenomenon>
-->

  <xsl:import href="WaterML1_1_common_to_waterml2.xsl"/>
  
  <xsl:output method="xml" indent="yes"/>
  <xsl:template name="VariablePhenomenaDictionaryEntry" match="wml:variable">
    <!-- callled from within a variable loop -->
    <xsl:param name="wfsBase"/>
    <xsl:param name="observedPropertiesBase"/>
    <xsl:param name="concept"/>
   
  <!--  <xsl:comment> Requirements Class:Reference needed</xsl:comment> -->
    <gml:dictionaryEntry>
      <gml:Definition>
        <xsl:attribute name="gml:id">
          <xsl:call-template name="VariableIdentifier">
            <xsl:with-param name="variable" select="."></xsl:with-param>
          </xsl:call-template>
        <!--  <xsl:value-of
            select="concat(translate(wml:variableCode[1]/@vocabulary,':','-'),'-',wml:variableCode[1])"
          />
          -->
        <!--  <xsl:value-of select="concat('concept-',$concept)"/> -->
        </xsl:attribute>
      <gml:description>
        <xsl:attribute name="xlink:href">
          <xsl:value-of
            select="concat($observedPropertiesBase,wml:variableCode[1]/@vocabulary,':',wml:variableCode[1])"
          />
        </xsl:attribute>
        <xsl:attribute name="xlink:title">
          <xsl:value-of select="wml:variableName"/>
        </xsl:attribute>
      </gml:description>      
        <gml:identifier> 
          <xsl:attribute name="codeSpace">http://hiscentral.cuahsi.org/wml/variable</xsl:attribute>
          <xsl:value-of
          select="concat(wml:variableCode[1]/@vocabulary,':',wml:variableCode[1])"
        /></gml:identifier> 

      <xsl:if test="$concept">
        <gml:name>
          <xsl:attribute name="codeSpace">http://hiscentral.cuahsi.org/ontology/</xsl:attribute>
          <xsl:value-of select="$concept"/>
        </gml:name>
      </xsl:if>
      <gml:name>
        <xsl:attribute name="codeSpace">
          <xsl:value-of
            select="concat('http://hiscentral.cuahsi.org/wml/vocabulary/',wml:variableCode[1]/@vocabulary)"
          />
        </xsl:attribute>
        
        <xsl:value-of select="wml:variableName"/>
        
      </gml:name>
      
      </gml:Definition>
      </gml:dictionaryEntry>
        
    
  </xsl:template>
  
  <xsl:template name="ObservedProperty" match="wml:timeSeriesResponse">
    <xsl:param name="wfsBase"/>
    <xsl:param name="observedPropertiesBase"/>
    <xsl:param name="concept"/>
   
    <swe:Phenomenon>
      <gml:description>
        <xsl:attribute name="xlink:href">
          <xsl:value-of
            select="concat($observedPropertiesBase,wml:variable/wml:variableCode[1]/@vocabulary,':',wml:variable/wml:variableCode[1])"
          />
        </xsl:attribute>
        <xsl:attribute name="xlink:title">
          <xsl:value-of select="wml:variable/wml:variableName"/>
        </xsl:attribute>
      </gml:description>
      <xsl:if test="$concept">
        <gml:name>
          <xsl:attribute name="codeSpace">
            http://hiscentral.cuahsi.org/ontology/
          </xsl:attribute>
          <xsl:value-of select="$concept"/>
        </gml:name>
      </xsl:if>
      <gml:name>
        <xsl:attribute name="codeSpace">
          <xsl:value-of
            select="concat('http://hiscentral.cuahsi.org/wml/vocabulary/',wml:variable/wml:variableCode[1]/@vocabulary)"
          />
        </xsl:attribute>

        <xsl:value-of select="wml:variable/wml:variableName"/>

      </gml:name>


    </swe:Phenomenon>

  </xsl:template>
  
  <xsl:template name="ObservablePropertyDictionaryEntry" match="wml:timeSeriesResponse">
    <xsl:param name="wfsBase"/>
    <xsl:param name="observedPropertiesBase"/>
    <xsl:param name="concept"/>
    <xsl:comment> Using ObservableProperty spec</xsl:comment>
    <op:ComplexObservableProperty gml:id="daily_mean_water_temp">
      <op:label>$concept</op:label> <!-- needs to be improved with stat information -->
      <op:basePhenomenon>
        <xsl:attribute name="xlink:href">
          <xsl:value-of select="concat(&quot;urn:cuashi/ontology&quot;,$concept)"/>
        </xsl:attribute>
        <xsl:attribute name="xlink:title">
          <xsl:value-of select="$concept"/>
        </xsl:attribute>
      </op:basePhenomenon> 
      <xsl:choose>
        <!-- use http://www.uncertml.org/ -->
        <xsl:when test="wml:variable/wml:dataType = 'Average'">
      <!-- Daily mean --> 
      <op:qualifier>
        <op:StatisticalQualifier gml:id="Average">
          <op:statisticalOperator xlink:href="http://www.uncertml.org/statistics/mean"/>
          <op:statisticalPeriod>
            
              <xsl:call-template name="TimeUnitToPeriod">
                <xsl:with-param name="TimeSupport" select="wml:variable/wml:timeScale/wml:timeSupport"/>
                <xsl:with-param name="Unit"  select="wml:variable/wml:timeScale/wml:unit"/>
              </xsl:call-template>
            </op:statisticalPeriod>
        </op:StatisticalQualifier>
      </op:qualifier>
    </xsl:when>
      </xsl:choose>    
    </op:ComplexObservableProperty>

    
  </xsl:template>

  
</xsl:stylesheet>
