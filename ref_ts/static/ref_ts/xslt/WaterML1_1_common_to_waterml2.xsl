<?xml version="1.0" encoding="UTF-8"?>
<!-- Created with Liquid XML Studio Developer Edition (Education) 9.0.11.3078 (http://www.liquid-technologies.com) -->
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:wml2="http://www.opengis.net/waterml/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:wml="http://www.cuahsi.org/waterML/1.1/"
    xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:om="http://www.opengis.net/om/2.0" xmlns:swe="http://www.opengis.net/swe/2.0"
    xmlns:sf="http://www.opengis.net/sampling/2.0"
    xmlns:sams="http://www.opengis.net/samplingSpatial/2.0"
    xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" 
    xmlns:gmd="http://www.isotc211.org/2005/gmd" 
    xmlns:gco="http://www.isotc211.org/2005/gco" 
    xmlns:gss="http://www.isotc211.org/2005/gss"
    version="1.0">
    
    <xsl:import href="HisCVConversions/HisUnits.xslt" />
    <xsl:import href="HisCVConversions/HisOntologyMapper.xslt" />
    
    <doc xmlns="http://www.oxygenxml.com/ns/doc/xsl">
        <desc>This includes vocabulary translaotion and other elements</desc>
    </doc>    
   
    <xsl:template name="mapCensorCode">
        <xsl:param name="censorCode"></xsl:param>
    <!--    Quality	OGC Name	Description	
        Good	http://www.opengis.net/def/waterml/2.0/quality/good 
        The data has been examined and represents a reliable measurement.	not censored
        non-detect
        Suspect	http://www.opengis.net/def/waterml/2.0/quality/suspect
        The data should be treated as suspect.	present but not quantified
        Estimate	http://www.opengis.net/def/waterml/2.0/quality/estimate
        The data is an estimate only, not a direct measurement. 	less than
        greater than
       -->
        <xsl:choose>
            <xsl:when test="$censorCode='not censored' or
                $censorCode='non-detect'">
                <xsl:call-template name="QualityElement">
                    <xsl:with-param name="href">http://www.opengis.net/def/waterml/2.0/quality/good</xsl:with-param>
                    <xsl:with-param name="title"><xsl:value-of select="$censorCode"/></xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$censorCode='present but not quantified'">
                <xsl:call-template name="QualityElement">
                    <xsl:with-param name="href">http://www.opengis.net/def/waterml/2.0/quality/suspect</xsl:with-param>
                    <xsl:with-param name="title">Suspect</xsl:with-param>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$censorCode='less than' or
                $censorCode='greater than'">
                <xsl:call-template name="QualityElement">
                    <xsl:with-param name="href">http://www.opengis.net/def/waterml/2.0/quality/estimate</xsl:with-param>
                    <xsl:with-param name="title"><xsl:value-of select="$censorCode"/></xsl:with-param>
                </xsl:call-template>
            </xsl:when>  
          <xsl:otherwise>
                <xsl:call-template name="QualityElement">
                    <xsl:with-param name="href">http://hiscentral.cuahsi.org/wml/censored/<xsl:value-of select="$censorCode"></xsl:value-of></xsl:with-param>
                    <xsl:with-param name="title"></xsl:with-param>
                </xsl:call-template>
            </xsl:otherwise>
            
        </xsl:choose>
        
    </xsl:template>
    
    <xsl:template name="QualityElement">
        <xsl:param name="href"></xsl:param>
        <xsl:param name="title"></xsl:param>
        <!--    Quality	OGC Name	Description	
        Good	http://www.opengis.net/def/waterml/2.0/quality/good 
        The data has been examined and represents a reliable measurement.	not censored
        non-detect
        Suspect	http://www.opengis.net/def/waterml/2.0/quality/suspect
        The data should be treated as suspect.	present but not quantified
        Estimate	http://www.opengis.net/def/waterml/2.0/quality/estimate
        The data is an estimate only, not a direct measurement. 	less than
        greater than
       -->
        <wml2:quality> 
            <xsl:attribute name="xlink:href">
                <xsl:value-of
                    select="$href"
                />
            </xsl:attribute>
            <xsl:attribute name="xlink:title"> <xsl:value-of
                select="$title"
            /> </xsl:attribute>
        </wml2:quality>
    </xsl:template>
    
    <xsl:template name="TimeUnitToPeriod">
        <xsl:param name="Unit"/>
        <xsl:param name="TimeSupport"/>
        <xsl:choose>

            <xsl:when test="$Unit/wml:unitName = 'minute'">PT<xsl:value-of select="$TimeSupport"
                />M</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'min'">PT<xsl:value-of select="$TimeSupport"
                />M</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'minute'">PT<xsl:value-of
                    select="$TimeSupport"/>M</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'M'">PT<xsl:value-of select="$TimeSupport"
                />M</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'm'">PT<xsl:value-of select="$TimeSupport"
                />M</xsl:when>

            <xsl:when test="$Unit/wml:unitName = 'hour'">PT<xsl:value-of select="$TimeSupport"
                />H</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'h'">PT<xsl:value-of select="$TimeSupport"
                />H</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'hr'">PT<xsl:value-of select="$TimeSupport"
                />H</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'hour'">PT<xsl:value-of
                    select="$TimeSupport"/>H</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'h'">PT<xsl:value-of select="$TimeSupport"
                />H</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'hr'">PT<xsl:value-of select="$TimeSupport"
                />H</xsl:when>

            <xsl:when test="$Unit/wml:unitName = 'second'">PT<xsl:value-of select="$TimeSupport"
                />S</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'sec'">PT<xsl:value-of select="$TimeSupport"
                />S</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 's'">PT<xsl:value-of select="$TimeSupport"
                />S</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'second'">PT<xsl:value-of
                    select="$TimeSupport"/>S</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'sec'">PT<xsl:value-of
                    select="$TimeSupport"/>S</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 's'">PT<xsl:value-of select="$TimeSupport"
                />S</xsl:when>

            <xsl:when test="$Unit/wml:unitName = 'day'">P<xsl:value-of select="$TimeSupport"
                />D</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'd'">P<xsl:value-of select="$TimeSupport"
                />D</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'day'">P<xsl:value-of select="$TimeSupport"
                />D</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'd'">P<xsl:value-of select="$TimeSupport"
                />D</xsl:when>

            <xsl:when test="$Unit/wml:unitName = 'month'">P<xsl:value-of select="$TimeSupport"
                />M</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'mon'">P<xsl:value-of select="$TimeSupport"
                />M</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'month'">P<xsl:value-of
                    select="$TimeSupport"/>M</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'm'">P<xsl:value-of select="$TimeSupport"
                />M</xsl:when>

            <xsl:when test="$Unit/wml:unitName = 'year'">P<xsl:value-of select="$TimeSupport"
                />Y</xsl:when>
            <xsl:when test="$Unit/wml:unitName = 'yr'">P<xsl:value-of select="$TimeSupport"
                />Y</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'year'">P<xsl:value-of
                    select="$TimeSupport"/>Y</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'yr'">P<xsl:value-of select="$TimeSupport"
                />Y</xsl:when>
            <xsl:when test="$Unit/wml:unitAbbreviation = 'y'">P<xsl:value-of select="$TimeSupport"
                />Y</xsl:when>
        </xsl:choose>
    </xsl:template>


    <xsl:template name="DataTypeToInterpolationType">
        <xsl:param name="dataTypeName"/>
        <wml2:interpolationType>
            <!--      xlink:href="http://www.opengis.net/def/timeseriesType/WaterML/2.0/Continuous"
                xlink:title="Continuous/Instantaneous"/>
            -->
            <xsl:choose>
                <xsl:when test="$dataTypeName='mean' or $dataTypeName='Average'">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'AverageSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Average in succeeding interval
                        ($dataTypeName) </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Continuous' or $dataTypeName='Instantaneous ' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'Continuous')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Continuous </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Constant Over Interval' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'ConstSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Constant in succeeding interval
                        ($dataTypeName) </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Maximum' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'MaxSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Maximum in succeeding interval
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Minimum ' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'MinSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Minimum in succeeding interval
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Sporadic' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'Discontinuous')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Discontinuous </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Cumulative' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'TotalSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Instantaneous total ($dataTypeName)
                    </xsl:attribute>
                </xsl:when>
                <xsl:when test="$dataTypeName='Incremental' ">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'InstantTotal')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Succeeding total </xsl:attribute>
                </xsl:when>
                <xsl:when
                    test="$dataTypeName='Variance'
                    or $dataTypeName='StandardDeviation'
                    or $dataTypeName='Mode'
                    or $dataTypeName='Median'
                    or $dataTypeName='Best Easy Systematic Estimator'">
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://www.opengis.net/def/timeseriesType/WaterML/2.0/',
                            'ConstSucc')"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title"> Constant in succeeding interval (<xsl:value-of select="$dataTypeName"></xsl:value-of>) </xsl:attribute>
                </xsl:when>
                
                <xsl:when
                    test="wml:variable/wml:dataType">
                    <!-- last resort has datatype -->
                    <xsl:attribute name="xlink:href">
                        <xsl:value-of
                            select="concat('http://his.cuahsi.org/cv/dataType/',wml:variable/wml:dataType)"
                        />
                    </xsl:attribute>
                    <xsl:attribute name="xlink:title">
                        <xsl:value-of select="wml:variable/wml:dataType"/>
                    </xsl:attribute>
                </xsl:when>
                <xsl:otherwise>
                    
                        <xsl:attribute name="xlink:href">
                            <xsl:value-of
                                select="concat('http://his.cuahsi.org/cv/dataType/','unspecified')"
                            />
                        </xsl:attribute>
                        <xsl:attribute name="xlink:title">None Specified</xsl:attribute>
                    
                </xsl:otherwise>
            </xsl:choose>
        </wml2:interpolationType>
    </xsl:template>

<xsl:template name="SampleMediumMapper">
    <xsl:param name="SampleMedium"/>
    <!-- Medium	OGC Name
Water	http://www.opengis.net/def/waterml/2.0/medium/Water
Ground Water	http://www.opengis.net/def/waterml/2.0/medium/GroundWater
Surface Water	http://www.opengis.net/def/waterml/2.0/medium/SurfaceWater
Sediment	http://www.opengis.net/def/waterml/2.0/medium/SedimentWater
Pore Water	http://www.opengis.net/def/waterml/2.0/medium/PoreWater
Pore Air	http://www.opengis.net/def/waterml/2.0/medium/PoreAir
Soil	http://www.opengis.net/def/waterml/2.0/medium/Soil
Soil Air	http://www.opengis.net/def/waterml/2.0/medium/SoilAir 
Soil Water	http://www.opengis.net/def/waterml/2.0/medium/SoilWater 
Atmosphere	http://www.opengis.net/def/waterml/2.0/medium/Atmosphere 
Tissue	http://www.opengis.net/def/waterml/2.0/medium/Tissue
Ground snow	http://www.opengis.net/def/waterml/2.0/medium/GroundSnow
Unknown	http://www.opengis.net/def/waterml/2.0/medium/Unknown
-->
    <xsl:choose>
        <xsl:when test="$SampleMedium ='Water'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Water</xsl:with-param>
            </xsl:call-template>
          </xsl:when>
        <xsl:when test="$SampleMedium ='Groundwater'">
            
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/GroundWater</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Surface Water'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/SurfaceWater</xsl:with-param>
            </xsl:call-template>
         </xsl:when>
        <xsl:when test="$SampleMedium ='Sediment'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Sediment</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Pore Water'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/PoreWater</xsl:with-param>
            </xsl:call-template>
         </xsl:when>
        <xsl:when test="$SampleMedium ='Precipitation'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Atmosphere</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Snow'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Water</xsl:with-param>
            </xsl:call-template>
         </xsl:when>
        <xsl:when test="$SampleMedium ='Soil water'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/SoilWater</xsl:with-param>
            </xsl:call-template>
                   </xsl:when>
        <xsl:when test="$SampleMedium ='Tissue'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Tissue</xsl:with-param>
            </xsl:call-template>
         </xsl:when>
        <xsl:when test="$SampleMedium ='Pore Air'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/PoreAir</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Soil Air'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/SoilAir</xsl:with-param>
            </xsl:call-template>
         </xsl:when>
        <xsl:when test="$SampleMedium ='Ground snow'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/GroundSnow</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Unknown'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://www.opengis.net/def/waterml/2.0/medium/Unknown</xsl:with-param>
            </xsl:call-template>
        </xsl:when>
        <xsl:when test="$SampleMedium ='Other'">
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://hiscentral.cuahsi.org/wml/sampledMedium</xsl:with-param>
            </xsl:call-template> 
        </xsl:when>
        <xsl:otherwise>
            <xsl:call-template name="SampleMediumCreator">
                <xsl:with-param name="SampleMedium" select="$SampleMedium"></xsl:with-param>
                <xsl:with-param name="url" >http://hiscentral.cuahsi.org/wml/sampledMedium</xsl:with-param>
            </xsl:call-template>
         </xsl:otherwise>
    </xsl:choose>
</xsl:template>
    
    <xsl:template name="SampleMediumCreator">
        <xsl:param name="url">http://www.opengis.net/def/waterml/2.0/medium/Unknown</xsl:param>
        <xsl:param name="SampleMedium">Unknown</xsl:param>
        <wml2:sampledMedium>
            <xsl:attribute name="xlink:href"> 
                <xsl:value-of select="$url"></xsl:value-of>
            </xsl:attribute>
            <xsl:attribute name="xlink:title"> 
                <xsl:value-of select="$SampleMedium"></xsl:value-of>
            </xsl:attribute> 
        
            </wml2:sampledMedium>
    </xsl:template>
    
   <xsl:template name="UOMCreator">
        <xsl:param name="Unit"/>

        <xsl:choose>
            <xsl:when test="$Unit/wml:unitAbbreviation">
                <xsl:call-template name="UOMMapper">
                    <xsl:with-param name="UnitString" select="$Unit/wml:unitAbbreviation"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$Unit/wml:unitName">
                <xsl:call-template name="UOMMapper">
                    <xsl:with-param name="UnitString" select="$Unit/wml:unitName"/>
                </xsl:call-template>
            </xsl:when>
            <xsl:when test="$Unit/wml:unitCode">
                <xsl:call-template name="UOMMapper">
                    <xsl:with-param name="UnitString" select="$Unit/wml:unitCode"/>
                </xsl:call-template>
            </xsl:when>
           
            <xsl:otherwise>unitless</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- http://aurora.regenstrief.org/~ucum/ucum.html -->
    <xsl:template name="UOMMapper">
        <xsl:param name="UnitString"/>
       
        <xsl:choose>

            <xsl:when test="$UnitString = 'cubic feet per second'">ft^3/s</xsl:when>
            <xsl:when test="$UnitString = 'cfs'">ft^3/s</xsl:when>

            <xsl:when test="$UnitString = 'second'">s</xsl:when>
            <xsl:when test="$UnitString = 's'">s</xsl:when>
            <xsl:when test="$UnitString = 'sec'">s</xsl:when>

            <xsl:when test="$UnitString = 'deg C'">C</xsl:when>
            <xsl:when test="$UnitString = 'degC'">C</xsl:when>

            <xsl:when test="$UnitString = 'international foot'">[ft_i]</xsl:when>
            <xsl:when test="$UnitString = 'ft'">[ft_i]</xsl:when>

            <xsl:when test="$UnitString = 'uS/cm @25C'">uS/cm_[25C]</xsl:when>
            <xsl:when test="$UnitString = 'microsiemens per centimeter'">uS/cm</xsl:when>
            <xsl:when test="$UnitString = 'uS/cm'">uS/cm</xsl:when>

            <xsl:when test="$UnitString = 'volts'">V</xsl:when>
            <xsl:when test="$UnitString = 'V'">V</xsl:when>

            <xsl:when test="$UnitString = 'NTU'">[NTU]</xsl:when>
            <xsl:when test="$UnitString = 'nephelometric turbidity units'">[NTU]</xsl:when>

            <xsl:when test="$UnitString = 'milligrams per liter'">mg/L</xsl:when>
            <xsl:when test="$UnitString = 'mg/L'">mg/L</xsl:when>

            <xsl:when test="$UnitString = 'percent'">%</xsl:when>
            <xsl:when test="$UnitString = '%'">%</xsl:when>

            <xsl:when test="$UnitString = 'dimensionless'">[dimensionless]</xsl:when>
            <xsl:when test="$UnitString = '-'">[dimensionless]</xsl:when>

            <xsl:when test="$UnitString = 'count'">{TOT} </xsl:when>
            <xsl:when test="$UnitString = 'number'">{TOT} </xsl:when>
            
            <xsl:otherwise>
          
              <xsl:call-template name="HisUOMMapper">
                    <xsl:with-param name="UnitString">
                        <xsl:value-of select="$UnitString" /> 
                    </xsl:with-param>
                </xsl:call-template>
                  
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="cleanIdentifier">
        <xsl:param name="identifier"></xsl:param>
        <xsl:value-of
            select="translate($identifier,'/ =','-._')" />
      <!--  <xsl:value-of
            select="translate(translate(
            translate($identifier,'/','-'),
            ' ', '.'),
            '=','_')" />-->
    </xsl:template>
    
    <xsl:template name="MethodIdentifier">
        <xsl:param name="method"></xsl:param>
        <xsl:choose>
            <xsl:when test="$method/wml:MethodCode">
                <xsl:value-of select="concat($method/../../wml:sourceInfo/wml:siteCode/@network,'-',$method/wml:methodCode)" />
            </xsl:when>
            <xsl:when test="$method/@methodID">
                <xsl:value-of select="concat($method/../../wml:sourceInfo/wml:siteCode/@network,'-',$method/@methodID)" />
            </xsl:when> 
            <xsl:otherwise>
                <xsl:value-of select="concat($method/../../wml:sourceInfo/wml:siteCode/@network,'-','NoIdentifier')" /> 
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="SiteIdentifier">
        <xsl:param name="site"></xsl:param>
        <xsl:choose>
            <xsl:when test="$site/wml:siteCode">
                <xsl:value-of select="concat($site/wml:siteCode/@network,'-',$site/wml:siteCode)" />
            </xsl:when>
            <xsl:when test="$site/@siteID">
                <xsl:value-of select="concat($site/wml:siteCode/@network,'-',$site/@siteID)" />
            </xsl:when> 
            <xsl:otherwise>
                <xsl:value-of select="concat($site/wml:siteCode/@network,'-','NoIdentifier')" /> 
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <xsl:template name="VariableIdentifier">
        <xsl:param name="variable"></xsl:param>
        <xsl:value-of
            select="concat($variable/wml:variableCode[1]/@vocabulary,'.')" />
           <xsl:call-template name="cleanIdentifier">
               <xsl:with-param name="identifier" select="$variable/wml:variableCode[1]"></xsl:with-param>
           </xsl:call-template>
    </xsl:template>
    
    <xsl:template name="QualifierIdentifier">
        <xsl:param name="qualifier"></xsl:param>
         <xsl:value-of select="concat('qualifier-',translate($qualifier, &quot; &quot;, &quot;_&quot;))"
    /> 

    </xsl:template> 
    <xsl:template name="QualityControlIdentifier">
        
        
        <xsl:param name="qc"></xsl:param>
        <xsl:value-of select="concat('qclevel-',translate($qc, &quot; &quot;, &quot;_&quot;))"
        /> 
        
    </xsl:template>
    
    <xsl:template name="verticalDataumMapper">
        <!-- need to figure out OGC NZ mapping 
           horiz http://www.opengis.net/def/objectType/EPSG/0/code
            
            veritical crs:
            http://www.opengis.net/def/crs/EPSG/0/3163
            
             veritical datum:
            http://www.opengis.net/def/datum/EPSG/0/5100
            
            AU BOM
            http://www.bom.gov.au/water/wdtf/documentation/schema-control-lists/water-quality-sampling-depth-type.htm
            -->
        <xsl:param name="verticalDataum"></xsl:param>
        <xsl:choose>
            <xsl:when test="$verticalDataum='NAVD88'">http://www.opengis.net/def/datum/EPSG/0/5103</xsl:when>
            <xsl:when test="$verticalDataum='NGVD29'">http://www.opengis.net/def/datum/EPSG/0/5102</xsl:when>
            <xsl:when test="$verticalDataum='MSL'">http://www.opengis.net/def/datum/EPSG/0/5100</xsl:when>
            <xsl:when test="$verticalDataum='Unknown'">urn:ogc:def:datum:hiscentral.cuahsi.org::unknown</xsl:when>
            <xsl:otherwise>http://spatialreference.org/ref/sr-org/6707/</xsl:otherwise>
        </xsl:choose>
    </xsl:template>
</xsl:stylesheet>
