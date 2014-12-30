<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:someTrueP-Or="someTrueP-Or"
>
  <xsl:import href="someTrue.xsl"/>
  <xsl:import href="map.xsl"/>
  
  <someTrueP-Or:someTrueP-Or/>
  
  <xsl:variable name="someTrueP-Or:vP-Or" select="document('')/*/someTrueP-Or:*[1]"/>
  
  <xsl:template name="someTrueP">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pPredicate" select="/.."/>
    
    <xsl:variable name="vMappedList">
      <xsl:call-template name="map">
        <xsl:with-param name="pFun" select="$pPredicate"/>
        <xsl:with-param name="pList1" select="$pList"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="someTrue">
      <xsl:with-param name="pList" select="ext:node-set($vMappedList)/*"/>
      
    </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>