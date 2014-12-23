<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:myFun="f:myFun"
  exclude-result-prefixes="xsl myFun"
 >
 
  <!-- To be applied on any xml file -->
  <xsl:import href="findRoot.xsl"/>
  <xsl:import href="trignm.xsl"/>
  
  <xsl:output method="text"/>
  
  <myFun:myFun/>
 
  <xsl:template match="/">
    <xsl:call-template name="findRootBS">
      <xsl:with-param name="pFun" select="document('')/*/myFun:*[1]"/>
      <xsl:with-param name="pX1" select="0"/>
      <xsl:with-param name="pX2" select="$halfPi"/>
      <xsl:with-param name="pEps" select="0.000000001"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="myFun:*">
    <xsl:param name="arg1"/>
    
    <xsl:variable name="vSineX">
      <xsl:call-template name="sin">
        <xsl:with-param name="pX" select="$arg1"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vSineX - 0.5"/>
  </xsl:template>

</xsl:stylesheet>