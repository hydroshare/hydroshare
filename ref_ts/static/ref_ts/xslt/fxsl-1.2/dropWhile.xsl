<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
exclude-result-prefixes="xsl"
>
  <xsl:template name="dropWhile">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pContollerParam" select="/.."/>

    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[dropWhile]Error: pController not specified.</xsl:message>
    </xsl:if>   
    
      <xsl:if test="$pList">
	    <xsl:variable name="vDrop">
	      <xsl:apply-templates select="$pController">
	        <xsl:with-param name="pList" select="$pList[1]"/>
	        <xsl:with-param name="pParams" select="$pContollerParam"/>
	      </xsl:apply-templates>
	    </xsl:variable>
	    
	    <xsl:choose>
	    <xsl:when test="string($vDrop)">
	       <xsl:call-template name="dropWhile">
			  <xsl:with-param name="pList" select="$pList[position() > 1]" />
			  <xsl:with-param name="pController" select="$pController"/>
			  <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
	       </xsl:call-template>
	    </xsl:when>
	    <xsl:otherwise>
	      <xsl:copy-of select="$pList"/>
	    </xsl:otherwise>
	    </xsl:choose>
      
      </xsl:if>
  </xsl:template>

</xsl:stylesheet>