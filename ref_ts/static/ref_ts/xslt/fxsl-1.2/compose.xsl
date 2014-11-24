<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>
  
  <xsl:template name="compose">
    <xsl:param name="pFun1" select="/.."/>
    <xsl:param name="pFun2" select="/.."/>
    <xsl:param name="pArg1"/>
    
    <xsl:variable name="vrtfFun2">
      <xsl:apply-templates select="$pFun2">
        <xsl:with-param name="pArg1" select="$pArg1"/>
      </xsl:apply-templates>
    </xsl:variable>
    
    <xsl:apply-templates select="$pFun1">
      <xsl:with-param name="pArg1" select="ext:node-set($vrtfFun2)/node()"/>
    </xsl:apply-templates>
    
  </xsl:template>
</xsl:stylesheet>