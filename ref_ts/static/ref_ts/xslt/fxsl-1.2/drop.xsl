<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:template name="drop">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pN" select="0"/>
    
    <xsl:copy-of select="$pList[position() > $pN]"/>
  </xsl:template>

</xsl:stylesheet>