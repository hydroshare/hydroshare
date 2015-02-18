<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myIsAlpha="f:myIsAlpha"
>
 
  <xsl:import href="str-filterDVC.xsl"/>
  
  <!-- To be applied on testFilter90K.xml file -->
  <!-- Compare this with Mike Kay's ingenious solution:
      testDoubleTranslate.xsl -->
 
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <myIsAlpha:myIsAlpha/>
  
  <xsl:template match="/">
    <xsl:variable name="vIsAlpha" select="document('')/*/myIsAlpha:*[1]"/>
    
    Filtering by IsAlpha: 
    
    filter('A1b3C67DE+', IsAlpha) = 
    <!-- <xsl:variable name="vResult"> -->
	    <xsl:call-template name="str-filter">
		    <xsl:with-param name="pStr" select="string(/*)"/>
		    <xsl:with-param name="pController" select="$vIsAlpha"/>
	    </xsl:call-template>
    <!-- </xsl:variable> -->
   </xsl:template>
  
  <xsl:variable name="vUpper" select="'ABCDEFGHIJKLMNOPQRSTUVWXYZ'"/>
  <xsl:variable name="vLower" select="'abcdefghijklmnopqrstuvwxyz'"/>
  <xsl:variable name="vAlpha" select="concat($vUpper, $vLower)"/>
  
  <xsl:template name="myIsAlpha" match="myIsAlpha:*">
    <xsl:param name="arg1"/>
    
    <xsl:if test="contains($vAlpha, $arg1)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>