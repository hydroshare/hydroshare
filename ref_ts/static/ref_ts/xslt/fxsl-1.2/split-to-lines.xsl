<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:pGenerator="f:pGenerator"
xmlns:pController="f:pController" 
exclude-result-prefixes="xsl ext pGenerator pController" 
>
  <xsl:import href="buildListWhile.xsl"/> 

  <!-- To be applied on text.xml -->
  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <pGenerator:pGenerator/>
  <pController:pController/>

  <xsl:variable name="vMyGenerator" select="document('')/*/pGenerator:*[1]"/>
  <xsl:variable name="vMyController" select="document('')/*/pController:*[1]"/>
  
  <xsl:template match="/">
  
    <xsl:variable name="prtfSplitParams">
	    <lineLength>64</lineLength>
	    <text><xsl:value-of select="/*"/></text>
    </xsl:variable>
    
    <xsl:variable name="pSplitParams" select="ext:node-set($prtfSplitParams)"/>
    
    <xsl:variable name="vNumLines" 
                  select="ceiling(string-length($pSplitParams/text) 
                                div 
                                   $pSplitParams/lineLength
                                   )"
    />
	<xsl:call-template name="buildListWhile">
      <xsl:with-param name="pParam0" select="$pSplitParams"/>
	  <xsl:with-param name="pGenerator" select="$vMyGenerator"/>
      <xsl:with-param name="pController" select="$vMyController"/>
      <xsl:with-param name="pContollerParam" select="$vNumLines"/>
      <xsl:with-param name="pElementName" select="'line'"/>
	</xsl:call-template>
  </xsl:template>

  <xsl:template name="listGenerator" match="pGenerator:*">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:variable name="vLineLength" select="$pParams/lineLength"/>
     <xsl:variable name="vText" select="$pParams/text"/>
     <xsl:value-of select="substring($vText, count($pList) * $vLineLength, $vLineLength)"/>
  </xsl:template>
  
  <xsl:template name="listController" match="pController:*">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:if test="count($pList) &lt;= $pParams">1</xsl:if>
  </xsl:template>

</xsl:stylesheet>