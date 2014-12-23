<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:import href="reverse.xsl"/>
  
  <xsl:output method="text"/>
  
  <xsl:template match="/">
    <xsl:call-template name="strReverse">
      <xsl:with-param name="pStr" select="'abracadabra'"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>
