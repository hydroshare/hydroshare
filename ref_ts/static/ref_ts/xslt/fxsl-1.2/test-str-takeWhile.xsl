<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:MyTakeController="f:MyTakeController" 
exclude-result-prefixes="xsl MyTakeController"
>
  <xsl:import href="str-takeWhile.xsl"/>
  <xsl:import href="str-dropWhile.xsl"/>
  
  <!-- To be applied on: test-str-takeWhile.xml -->
  
  <MyTakeController:MyTakeController/>
  
  <xsl:output method="text"/>
  <xsl:template match="/">
    <xsl:variable name="vMyTakeController"
                  select="document('')/*/MyTakeController:*[1]"/>
    <xsl:call-template name="str-takeWhile">
      <xsl:with-param name="pStr" select="string(/*)"/>
      <xsl:with-param name="pController" select="$vMyTakeController"/>
      <xsl:with-param name="pContollerParam" select="0123456789"/>
    </xsl:call-template>
    <xsl:value-of select="'&lt;===>'"/>
    <xsl:call-template name="str-dropWhile">
      <xsl:with-param name="pStr" select="string(/*)"/>
      <xsl:with-param name="pController" select="$vMyTakeController"/>
      <xsl:with-param name="pContollerParam" select="0123456789"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="MyTakeController:*">
  	<xsl:param name="pChar" select="''"/>
    <xsl:param name="pParams" select="/.."/>
    
    <xsl:if test="contains($pParams, $pChar)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>
