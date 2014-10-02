<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>
  
  <xsl:template name="compose-flist">
    <xsl:param name="pFunList" select="/.."/>
    <xsl:param name="pArg1"/>
    
    <xsl:choose>
      <xsl:when test="not($pFunList)">
        <xsl:copy-of select="$pArg1"/>
      </xsl:when>
      <xsl:otherwise>
	    <xsl:variable name="vrtfFunRest">
	      <xsl:call-template name="compose-flist">
            <xsl:with-param name="pFunList" select="$pFunList[position() > 1]"/>
	        <xsl:with-param name="pArg1" select="$pArg1"/>
	      </xsl:call-template>
	    </xsl:variable>
	    
	    <xsl:apply-templates select="$pFunList[1]">
	      <xsl:with-param name="pArg1" select="ext:node-set($vrtfFunRest)/node()"/>
	    </xsl:apply-templates>
      </xsl:otherwise>
    </xsl:choose>

  </xsl:template>
</xsl:stylesheet>