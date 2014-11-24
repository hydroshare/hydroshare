<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:template name="split">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pN" select="0"/>
    <xsl:param name="pElementName" select="'list'"/>
    
    <xsl:element name="{$pElementName}">
	    <xsl:copy-of select="$pList[position() &lt;= $pN]"/>
    </xsl:element>
    <xsl:element name="{$pElementName}">
	    <xsl:copy-of select="$pList[position() > $pN]"/>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>