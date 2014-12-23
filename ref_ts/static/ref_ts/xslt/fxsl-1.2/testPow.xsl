<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" >
 
  <xsl:import href="pow.xsl"/> 

  <xsl:output method="text"/>
  
  <xsl:template match="/">
    <xsl:for-each select="(document('')//node())[position() &lt; 10]">
	    <xsl:value-of select="concat(position(), '^', position(),' = ')"/>
	    <xsl:call-template name="pow">
	      <xsl:with-param name="pTimes" select="position()"/>
	      <xsl:with-param name="pX" select="position()"/>
	    </xsl:call-template>
	    <xsl:text>&#xA;</xsl:text>
    </xsl:for-each>

	    <xsl:call-template name="pow">
	      <xsl:with-param name="pTimes" select="5000"/>
	      <xsl:with-param name="pX" select="1.0002"/>
	    </xsl:call-template>
      <xsl:message>The End</xsl:message>
  </xsl:template>

</xsl:stylesheet>