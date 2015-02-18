<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
exclude-result-prefixes="xsl"
>
  <xsl:template name="str-takeWhile">
    <xsl:param name="pStr" select="/.."/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pContollerParam" select="/.."/>

    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[str-takeWhile]Error: pController not specified.</xsl:message>
    </xsl:if>   
    
	    <xsl:variable name="vFirstChar" select="substring($pStr, 1, 1)"/>
	    <xsl:variable name="vAccept">
	      <xsl:apply-templates select="$pController">
	        <xsl:with-param name="pChar" select="$vFirstChar"/>
	        <xsl:with-param name="pParams" select="$pContollerParam"/>
	      </xsl:apply-templates>
	    </xsl:variable>
	    
	    <xsl:if test="string($vAccept)">
		   <xsl:value-of select="$vFirstChar"/>
	       <xsl:call-template name="str-takeWhile">
			  <xsl:with-param name="pStr" select="substring($pStr, 2)" />
			  <xsl:with-param name="pController" select="$pController"/>
			  <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
	       </xsl:call-template>
	    </xsl:if>
      
  </xsl:template>

</xsl:stylesheet>