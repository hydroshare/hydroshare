<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myAdd="f:myAdd"
xmlns:myParam="f:myParam"
>
  <xsl:import href="scanlDVC.xsl"/>
  <xsl:output omit-xml-declaration="yes" indent="yes"/>

  <!-- To be applied on: numList.xml -->
  <myAdd:myAdd/>
  
  <myParam:myParam>0</myParam:myParam>
  
  <xsl:template match="/">
   
    <xsl:variable name="vFun" select="document('')/*/myAdd:*[1]"/>
    <xsl:variable name="vZero" select="document('')/*/myParam:*[1]"/>

    
    <xsl:call-template name="scanl">
      <xsl:with-param name="pFun" select="$vFun"/>
      <xsl:with-param name="pQ0" select="$vZero" />
      <xsl:with-param name="pList" select="/*/num"/>
    </xsl:call-template>
    
    - - - - - - - - - - -
    
     <xsl:call-template name="scanl1">
      <xsl:with-param name="pFun" select="$vFun"/>
      <xsl:with-param name="pList" select="/*/num"/>
    </xsl:call-template>
    
  </xsl:template>
  
  <xsl:template match="myAdd:*">
    <xsl:param name="pArg1" select="0"/>
    <xsl:param name="pArg2" select="0"/>
  
    <xsl:value-of select="$pArg1 + $pArg2"/>
  </xsl:template>
  
</xsl:stylesheet>