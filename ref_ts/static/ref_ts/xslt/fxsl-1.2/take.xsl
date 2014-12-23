<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:take-controller="take-controller"
xmlns:take-dynamic-controller="take-dynamic-controller"
exclude-result-prefixes="xsl"
>
  <xsl:import href="buildListWhile.xsl"/>
  <take-controller:take-controller/>
  <take-dynamic-controller:take-dynamic-controller/>
 
  <xsl:template name="take">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pN" select="0"/>
    <xsl:param name="pGenerator" select="/.."/>
    <xsl:param name="pParam0" select="/.."/>
    <xsl:param name="pParamGenerator" select="/.."/>
    <xsl:param name="pElementName" select="'el'"/>
    
    <xsl:variable name="vTakeController" select="document('')/*/take-controller:*[1]"/>
    <xsl:variable name="vTakeDynController" select="document('')/*/take-dynamic-controller:*[1]"/>

    <xsl:choose>
      <xsl:when test="$pList">
	    <xsl:copy-of select="$pList[position() &lt;= $pN]"/>
      </xsl:when>
      <xsl:when test="$pGenerator">
		  <xsl:call-template name="buildListWhile">
			    <xsl:with-param name="pList" select="/.."/>
			    <xsl:with-param name="pGenerator" select="$pGenerator"/>
			    <xsl:with-param name="pController" select="$vTakeDynController"/>
			    <xsl:with-param name="pContollerParam" select="$pN"/>
			    <xsl:with-param name="pParam0" select="$pParam0"/>
			    <xsl:with-param name="pParamGenerator" select="$pParamGenerator"/>
			    <xsl:with-param name="pElementName" select="$pElementName"/>
		  </xsl:call-template>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="takeController" match="*[namespace-uri()='take-controller']">
     <xsl:param name="pParams"/>
     
     <xsl:if test="$pParams > 0">1</xsl:if>
  </xsl:template>
  
  <xsl:template name="takeDynController" match="*[namespace-uri()='take-dynamic-controller']">
     <xsl:param name="pList"/>
     <xsl:param name="pParams"/>
     
     <xsl:if test="$pParams >= count($pList)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>