<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:auxSums="f:auxSums"
 xmlns:zeroSums="f:zeroSums" 
 exclude-result-prefixes="xsl ext auxSums zeroSums"
>
 <xsl:import href="scanlDVC.xsl"/>
  
 <!-- To be applied on: numList.xml -->
 
 <xsl:output omit-xml-declaration="yes" indent="yes"/>

  <auxSums:auxSums/>
  
  <zeroSums:zeroSums>
    <s>0</s>
    <sq>0</sq>
  </zeroSums:zeroSums>

  <xsl:template match="/">
    <xsl:variable name="vZeroSums" select="document('')/*/zeroSums:*[1]"/>
    <xsl:variable name="vfAuxSums" select="document('')/*/auxSums:*[1]"/>
    
    <xsl:variable name="vrtf-auxSums">
      <xsl:call-template name="scanl">
        <xsl:with-param name="pFun" select="$vfAuxSums"/>
        <xsl:with-param name="pQ0" select="$vZeroSums"/>
        <xsl:with-param name="pList" select="/*/*"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:copy-of select="ext:node-set($vrtf-auxSums)/*"/>

  </xsl:template>
  
  <xsl:template match="auxSums:*">
    <xsl:param name="pArg1" select="/.."/> <!--P0-->
    <xsl:param name="pArg2" /> 
    
     <s><xsl:value-of select="$pArg1/s + $pArg2"/></s>
     <sq><xsl:value-of select="$pArg1/sq + $pArg2 * $pArg2"/></sq>
    
  </xsl:template>
  
</xsl:stylesheet>