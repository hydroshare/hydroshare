<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
xmlns:wml2="http://www.opengis.net/waterml/2.0"
xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:om="http://www.opengis.net/om/2.0"
xmlns:xlink="http://www.w3.org/1999/xlink"
xmlns:wml="http://www.cuahsi.org/waterML/1.1/" 
xmlns:fn="http://www.w3.org/2005/xpath-functions" 
xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs" version="2.0">
  <xsl:output method="xml" indent="yes" />
  <xsl:template match="wml:variablesResponse">

   
            <xsl:copy-of select="wml:variables"/>
      
    </xsl:template>
  
</xsl:stylesheet>
