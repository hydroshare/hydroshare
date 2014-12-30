<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>
  <xsl:import href="improve.xsl"/> 

  <!-- To be applied on diff-results.xml -->

  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <xsl:template match="/">
  
      <xsl:variable name="vrtfI1">
	    <xsl:call-template name="improve">
	      <xsl:with-param name="pList" select="/*/*[position() > 1]"/>
	    </xsl:call-template>
    </xsl:variable>
    Improve 1:
    <xsl:copy-of select="ext:node-set($vrtfI1)/*"/>
    <xsl:variable name="vrtfI2">
	    <xsl:call-template name="improve">
	      <xsl:with-param name="pList" select="ext:node-set($vrtfI1)/*"/>
	    </xsl:call-template>
    </xsl:variable>
    Improve 2:
    <xsl:copy-of select="ext:node-set($vrtfI2)/*"/>

    <xsl:variable name="vrtfI3">
	    <xsl:call-template name="improve">
	      <xsl:with-param name="pList" select="ext:node-set($vrtfI2)/*"/>
	    </xsl:call-template>
    </xsl:variable>
    Improve 3:
    <xsl:copy-of select="ext:node-set($vrtfI3)/*"/>

    <xsl:variable name="vrtfI4">
	    <xsl:call-template name="improve">
	      <xsl:with-param name="pList" select="ext:node-set($vrtfI3)/*"/>
	    </xsl:call-template>
    </xsl:variable>
    Improve 4:
    <xsl:copy-of select="ext:node-set($vrtfI4)/*"/>

  </xsl:template>

</xsl:stylesheet>