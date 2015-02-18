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

    <xsl:if test="$pStr">
      <xsl:variable name="vthisChar" select="substring($pStr, 1, 1)"/>
		  
		  <xsl:variable name="vHolds">
		    <xsl:apply-templates select="$pController">
		      <xsl:with-param name="arg1" select="$vthisChar"/>
		    </xsl:apply-templates>
		  </xsl:variable>
	    
	    <xsl:if test="string($vHolds)">
	      <xsl:copy-of select="$vthisChar"/>
	    </xsl:if>
	    
	    <xsl:call-template name="_str-filter">
	      <xsl:with-param name="pStr" select="substring($pStr, 2)"/>
	      <xsl:with-param name="pController" select="$pController"/>
	    </xsl:call-template>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>