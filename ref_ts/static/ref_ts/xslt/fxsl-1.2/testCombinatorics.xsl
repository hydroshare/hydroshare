<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 exclude-result-prefixes="xsl"
 >

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->

  <xsl:import href="combinatorics.xsl"/>
  
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
   
  <xsl:template match="/">
      <test>
		    <xsl:call-template name="cartProduct">
		      <xsl:with-param name="pLists" select="/test1/*"/>
		    </xsl:call-template>
     </test>
	  </xsl:template>
</xsl:stylesheet>