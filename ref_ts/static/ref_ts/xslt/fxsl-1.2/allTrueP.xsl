<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>
  <xsl:import href="map.xsl"/>
  <xsl:import href="allTrue.xsl"/>

  <xsl:template name="allTrueP">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pPredicate" select="/.."/>
    
    <xsl:variable name="vMappedList">
      <xsl:call-template name="map">
        <xsl:with-param name="pFun" select="$pPredicate"/>
        <xsl:with-param name="pList1" select="$pList"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="allTrue">
      <xsl:with-param name="pList" select="ext:node-set($vMappedList)/*"/>
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>