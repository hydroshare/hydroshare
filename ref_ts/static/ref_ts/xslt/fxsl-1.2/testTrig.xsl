<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
 
 <xsl:import href="trignm.xsl"/>
 <!-- To be applied on any xml file -->

 <xsl:output method="text"/>
  
  <xsl:template match="/">
	 <xsl:call-template name="cos">
	    <xsl:with-param name="pX" select="240"/>
        <xsl:with-param name="pUnit" select="'deg'"/>
	 </xsl:call-template>
  
  </xsl:template>
</xsl:stylesheet>