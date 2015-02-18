<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 
  <xsl:import href="exp.xsl"/>
 <!-- To be applied on any xml file -->

  <xsl:output method="text"/>
  
  <xsl:template match="/">
  <xsl:variable name="vPi" select="3.1415926535897932384626433832795"/>
  <xsl:variable name="vE" select="2.71828182845904"/>

    <xsl:call-template name="pow">
      <xsl:with-param name="pBase" select="1024"/>
      <xsl:with-param name="pPower" select=".1"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>