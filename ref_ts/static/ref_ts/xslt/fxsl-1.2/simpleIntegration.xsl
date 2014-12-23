<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
exclude-result-prefixes="xsl ext"
>
  <xsl:import href="PartialSumsList.xsl"/>
  
  <xsl:template name="simpleIntegration">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pA"/>
    <xsl:param name="pB"/>
    <xsl:param name="pEpsRough" select="0.0001"/>

     <xsl:variable name="vrtfRoughResults">
	    <xsl:call-template name="partialSumsList">
		    <xsl:with-param name="pFun" select="$pFun"/>
		    <xsl:with-param name="pA" select="$pA"/>
		    <xsl:with-param name="pB" select="$pB"/>
		    <xsl:with-param name="pEps" select="$pEpsRough"/>
	    </xsl:call-template>
     </xsl:variable>

     <xsl:variable name="vRoughResults" select="ext:node-set($vrtfRoughResults)/*"/>

	 <xsl:copy-of select="$vRoughResults"/>
	
  </xsl:template>

</xsl:stylesheet>