<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:someTrue-Or="someTrue-Or"
>
  <xsl:import href="foldr.xsl"/>
  
  <someTrue-Or:someTrue-Or/>
  
  <xsl:template name="someTrue">
    <xsl:param name="pList" select="/.."/>
    
    <xsl:variable name="vOr" select="document('')/*/someTrue-Or:*[1]"/>
    
    <xsl:call-template name="foldr">
      <xsl:with-param name="pFunc" select="$vOr"/>
      <xsl:with-param name="pA0" select="''"/>
      <xsl:with-param name="pList" select="$pList"/>
      
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="Or" match="*[namespace-uri()='someTrue-Or']">
    <xsl:param name="arg1"/>
    <xsl:param name="arg2"/>
    
    <xsl:if test="$arg1/node() or string($arg2)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>