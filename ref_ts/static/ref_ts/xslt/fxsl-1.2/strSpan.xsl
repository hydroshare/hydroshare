<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:import href="str-takeWhile.xsl"/>
  
  <xsl:template name="strSpan">
    <xsl:param name="pStr" />
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pContollerParam" select="/.."/>
    <xsl:param name="pElementName1" select="'el1'"/>
    <xsl:param name="pElementName2" select="'el2'"/>
    
    <xsl:variable name="vPositive">
	    <xsl:call-template name="str-takeWhile">
		    <xsl:with-param name="pStr" select="$pStr"/>
		    <xsl:with-param name="pController" select="$pController"/>
		    <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:element name="{$pElementName1}">
      <xsl:copy-of select="$vPositive"/>
    </xsl:element>
    
    <xsl:element name="{$pElementName2}">
	    <xsl:copy-of select="substring($pStr, string-length($vPositive) + 1)"/>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>