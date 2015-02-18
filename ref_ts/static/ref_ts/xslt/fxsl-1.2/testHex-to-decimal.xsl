<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:import href="hex-to-decimal.xsl"/>
  
  <xsl:output method="text"/>
  
  <xsl:template match="/">
    <xsl:call-template name="hex-to-decimal">
      <xsl:with-param name="pxNumber" select="/*/*[1]"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>

