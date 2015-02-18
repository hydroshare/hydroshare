<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 
  <xsl:output method="text"/>
  
  <!-- To be run on the testFilterxxK.xml files -->
  <!-- this ingenious double translate solution 
       belongs to Mike Kay                      -->
  
  <xsl:variable name="vUpper" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <xsl:variable name="vLower" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="vAlpha" select="concat($vUpper, $vLower)"/>
  
  <xsl:variable name="x" select="string(/*)"/>

  <xsl:template match="/">
    <xsl:value-of 
    select="translate($x, 
                      translate($x, $vAlpha, ''), '')"/>
  </xsl:template>
</xsl:stylesheet>