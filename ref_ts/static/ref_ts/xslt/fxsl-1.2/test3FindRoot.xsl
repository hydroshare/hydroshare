<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:myFun="f:myFun"
 xmlns:myFunPrim="f:myFunPrim" 
 exclude-result-prefixes="xsl myFun myFunPrim"
 >
 
  <xsl:import href="findRoot.xsl"/>
  <xsl:import href="trignm.xsl"/>
  <xsl:import href="exp.xsl"/>
   
  <xsl:output method="text"/>
  
  <myFun:myFun/>
  <myFunPrim:myFunPrim/>
 
  <xsl:template match="/">
    
    <xsl:call-template name="findRootBS">
      <xsl:with-param name="pFun" select="document('')/*/myFun:*[1]"/>
      <xsl:with-param name="pX2" select="4.71238898"/>   <!-- 3pi/2 -->
      <xsl:with-param name="pX1" select="7.85398163397"/><!-- 5pi/2 -->
      <xsl:with-param name="pEps" select="0.0001"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="myFun:*">
    <xsl:param name="arg1"/>
    
    <xsl:variable name="vSin">
	    <xsl:call-template name="sin">
	      <xsl:with-param name="pX" select="$arg1"/>
	      <xsl:with-param name="pEps" select="0.00001"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vSin "/>
  </xsl:template>

  <xsl:template match="myFunPrim:*">
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="2 * $arg1"/>
  </xsl:template>
</xsl:stylesheet>