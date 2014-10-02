<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:myAdd="f:myAdd"
>
  <xsl:import href="zipWith3.xsl"/>
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  
  <!-- To be applied on: numList.xml -->
  
  <myAdd:myAdd/>
  
  <xsl:template match="/">
    <xsl:variable name="vFun" select="document('')/*/myAdd:*[1]"/>

    <xsl:call-template name="zipWith3">
      <xsl:with-param name="pFun" select="$vFun"/>
      <xsl:with-param name="pList1" select="(/*/*)[position() &lt; 4]"/>
      <xsl:with-param name="pList2" select="(/*/*)[position() >= 4
                                                and position() &lt; 7]"/>
      <xsl:with-param name="pList3" select="(/*/*)[position() >= 7]"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template match="myAdd:*">
    <xsl:param name="arg1"/>
    <xsl:param name="arg2"/>
    <xsl:param name="arg3"/>

    <xsl:value-of select="$arg1 + $arg2 + $arg3"/>
  </xsl:template>

</xsl:stylesheet>