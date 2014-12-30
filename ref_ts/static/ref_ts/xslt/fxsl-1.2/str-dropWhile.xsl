<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
exclude-result-prefixes="xsl"
>
  <xsl:template name="str-dropWhile">
    <xsl:param name="pStr" select="''"/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pContollerParam" select="/.."/>

    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[str-dropWhile]Error: pController not specified.</xsl:message>
    </xsl:if>   
    
      <xsl:if test="$pStr">
	    <xsl:variable name="vDrop">
	      <xsl:apply-templates select="$pController">
	        <xsl:with-param name="pChar" select="substring($pStr, 1, 1)"/>
	        <xsl:with-param name="pParams" select="$pContollerParam"/>
	      </xsl:apply-templates>
	    </xsl:variable>
	    
	    <xsl:choose>
	    <xsl:when test="string($vDrop)">
	       <xsl:call-template name="str-dropWhile">
			  <xsl:with-param name="pStr" select="substring($pStr, 2)" />
			  <xsl:with-param name="pController" select="$pController"/>
			  <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
	       </xsl:call-template>
	    </xsl:when>
	    <xsl:otherwise>
	      <xsl:copy-of select="$pStr"/>
	    </xsl:otherwise>
	    </xsl:choose>
      
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>