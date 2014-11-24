<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

  <xsl:template name="str-filter">
    <xsl:param name="pStr"/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pElName" select="'str'"/>
    
    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[str-filter]Error: pController not specified.</xsl:message>
    </xsl:if>
    
    <xsl:element name="{$pElName}">
      <xsl:call-template name="_str-filter">
        <xsl:with-param name="pStr" select="$pStr"/>
        <xsl:with-param name="pController" select="$pController"/>
      </xsl:call-template>
    </xsl:element>

  </xsl:template>    

  <xsl:template name="_str-filter">
    <xsl:param name="pStr" />
    <xsl:param name="pController" select="/.."/>
    
    <xsl:variable name="vLen" select="string-length($pStr)"/>

    <xsl:choose>
	    <xsl:when test="$vLen = 1">
	  
			  <xsl:variable name="vHolds">
			    <xsl:apply-templates select="$pController">
			      <xsl:with-param name="arg1" select="$pStr"/>
			    </xsl:apply-templates>
			  </xsl:variable>
		    
		    <xsl:if test="string($vHolds)">
		      <xsl:copy-of select="$pStr"/>
		    </xsl:if>
	    </xsl:when>
	    <xsl:when test="$vLen > 1">
	      <xsl:variable name="vHalf" select="floor($vLen div 2)"/>
		    
		    <xsl:call-template name="_str-filter">
		      <xsl:with-param name="pStr" select="substring($pStr, 1, $vHalf)"/>
		      <xsl:with-param name="pController" select="$pController"/>
		    </xsl:call-template>
		    
		    <xsl:call-template name="_str-filter">
		      <xsl:with-param name="pStr" select="substring($pStr, $vHalf + 1)"/>
		      <xsl:with-param name="pController" select="$pController"/>
		    </xsl:call-template>
	    </xsl:when>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>