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
  

  <xsl:import href="WaterML1_1_site_to_WaterML2.xsl" />
  
  <xsl:param name="comments">false</xsl:param>
  
  <xsl:output method="xml" indent="yes"/> 
  
  <xsl:template match="wml:sitesResponse">
    <sam:SF_SamplingFeatureCollection>
      
      <xsl:for-each select="wml:site">
        <sam:member>
          <xsl:call-template name="SiteInfoToWaterObservationPoint">
            <xsl:with-param name="sourceInfoType" select="./wml:siteInfo"
              > </xsl:with-param>
          </xsl:call-template>
        
        </sam:member>
      </xsl:for-each>
        
    </sam:SF_SamplingFeatureCollection>
      
    
  </xsl:template>
 

</xsl:stylesheet>
