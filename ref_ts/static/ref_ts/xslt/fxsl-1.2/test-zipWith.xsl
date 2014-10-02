<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:myAdd="f:myAdd"
>
  <xsl:import href="zipWithDVC.xsl"/>
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  
  <!-- To be applied on: numList.xml -->
  <myAdd:myAdd/>
  <xsl:template match="/">
    <xsl:variable name="vFun" select="document('')/*/myAdd:*[1]"/>

    <xsl:call-template name="zipWith">
      <xsl:with-param name="pFun" select="$vFun"/>
      <xsl:with-param name="pList1" select="(/*/*)[position() &lt; 6]"/>
      <xsl:with-param name="pList2" select="(/*/*)[position() > 5]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="myAdd:*">
    <xsl:param name="pArg1"/>
    <xsl:param name="pArg2"/>

    <xsl:value-of select="$pArg1 + $pArg2"/>
  </xsl:template>

</xsl:stylesheet>