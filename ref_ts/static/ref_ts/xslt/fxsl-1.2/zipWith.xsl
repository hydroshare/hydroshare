<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:template name="zipWith">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pList1" select="/.."/>
    <xsl:param name="pList2" select="/.."/>
    <xsl:param name="pElName" select="'el'"/>

    <xsl:if test="$pList1 and $pList2">
      <xsl:variable name="vFunResult">
        <xsl:apply-templates select="$pFun">
          <xsl:with-param name="pArg1" select="$pList1[1]"/>
          <xsl:with-param name="pArg2" select="$pList2[1]"/>
        </xsl:apply-templates>
      </xsl:variable>

      <xsl:element name="{$pElName}">
        <xsl:copy-of select="$vFunResult"/>
      </xsl:element>
      
      <xsl:call-template name="zipWith">
        <xsl:with-param name="pFun" select="$pFun"/>
        <xsl:with-param name="pList1" select="$pList1[position() > 1]"/>
        <xsl:with-param name="pList2" select="$pList2[position() > 1]"/>
        <xsl:with-param name="pElName" select="'el'"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>

