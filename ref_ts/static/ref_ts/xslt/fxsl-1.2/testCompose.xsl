<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myFun1="f:myFun1"
xmlns:myFun2="f:myFun2" 
xmlns:ext="http://exslt.org/common"
exclude-result-prefixes="xsl ext myFun1 myFun2"
>
  <xsl:import href="compose.xsl"/>
  <xsl:import href="compose-flist.xsl"/>
  
  <!-- to be applied on any xml source -->
  
  <xsl:output method="text"/>
  <myFun1:myFun1/>
  <myFun2:myFun2/>


  <xsl:template match="/">
  
    <xsl:variable name="vFun1" select="document('')/*/myFun1:*[1]"/>
    <xsl:variable name="vFun2" select="document('')/*/myFun2:*[1]"/>
    Compose:
    (*3).(*2) 3 = 
    <xsl:call-template name="compose">
      <xsl:with-param name="pFun1" select="$vFun1"/>
      <xsl:with-param name="pFun2" select="$vFun2"/>
      <xsl:with-param name="pArg1" select="3"/>
    </xsl:call-template>
    
    <xsl:variable name="vrtfParam">
      <xsl:copy-of select="$vFun1"/>
      <xsl:copy-of select="$vFun2"/>
      <xsl:copy-of select="$vFun1"/>
    </xsl:variable>
    
    Multi Compose:
    (*3).(*2).(*3) 2 = 
    <xsl:call-template name="compose-flist">
      <xsl:with-param name="pFunList" select="ext:node-set($vrtfParam)/*"/>
      <xsl:with-param name="pArg1" select="2"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="myFun1:*">
    <xsl:param name="pArg1"/>
    
    <xsl:value-of select="3 * $pArg1"/>
  </xsl:template>

  <xsl:template match="myFun2:*">
    <xsl:param name="pArg1"/>
    
    <xsl:value-of select="2 * $pArg1"/>
  </xsl:template>
</xsl:stylesheet>