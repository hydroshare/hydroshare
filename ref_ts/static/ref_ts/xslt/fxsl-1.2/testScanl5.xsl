<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myAdd="f:myAdd"
xmlns:myParam="f:myParam"
>
  <xsl:import href="scanlDVC.xsl"/>
  <!-- to be applied on testScanl5.xml -->
  
  <xsl:output omit-xml-declaration="yes" indent="yes"/>

  <myParam:myParam>0</myParam:myParam>
  
  <xsl:template match="/">
   
    <xsl:variable name="vFun" select="document('')/*/myAdd:*[1]"/>
    <xsl:variable name="vZero" select="document('')/*/myParam:*[1]"/>

    
    <xsl:call-template name="scanl">
      <xsl:with-param name="pFun" select="$vFun"/>
      <xsl:with-param name="pQ0" select="$vZero" />
      <xsl:with-param name="pList" select="/*/entity"/>
      <xsl:with-param name="pElName" select="'subTotal'"/>
    </xsl:call-template>
  </xsl:template>
    
  <myAdd:myAdd/>
  <xsl:template match="myAdd:*">
    <xsl:param name="pArg1" select="0"/>
    <xsl:param name="pArg2" select="0"/>
  
    <xsl:value-of select="$pArg1 + sum($pArg2/row/someValue)"/>
  </xsl:template>
  
</xsl:stylesheet>