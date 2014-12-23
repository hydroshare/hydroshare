<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:pGenerator="pGenerator"
xmlns:pController="pController" 
exclude-result-prefixes="xsl pGenerator pController" 
>
  <xsl:import href="buildListWhile.xsl"/> 
  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <pGenerator:pGenerator/>
  <pController:pController/>

  <xsl:variable name="vMyGenerator" select="document('')/*/pGenerator:*[1]"/>
  <xsl:variable name="vMyController" select="document('')/*/pController:*[1]"/>
  
  <xsl:template match="/">
	<xsl:call-template name="buildListWhile">
	  <xsl:with-param name="pGenerator" select="$vMyGenerator"/>
      <xsl:with-param name="pController" select="$vMyController"/>
      <xsl:with-param name="pContollerParam" select="10"/>
      <xsl:with-param name="pElementName" select="'indoctrinate'"/>
	</xsl:call-template>
  </xsl:template>

  <xsl:template name="listGenerator" match="*[namespace-uri()='pGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     I should understand loops as being syntax for a simple form of
     recursion.
  </xsl:template>
  
  <xsl:template name="listController" match="*[namespace-uri()='pController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:if test="count($pList) &lt;= $pParams">1</xsl:if>
  </xsl:template>

</xsl:stylesheet>