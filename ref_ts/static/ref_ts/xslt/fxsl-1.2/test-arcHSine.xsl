<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:import href="arcHTrignm.xsl"/>
  
  <xsl:output method="text"/>
  
  <xsl:template match="/">
    <xsl:call-template name="archcos">
      <xsl:with-param name="pX" select="1.1276259652063807852262251614027"/>
      <xsl:with-param name="pEps" select="0.0000000001"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>