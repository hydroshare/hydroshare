<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:MyWithinEpsController="MyWithinEpsController"
exclude-result-prefixes="xsl ext MyWithinEpsController" 
>

  <xsl:import href="buildListWhile.xsl"/>

  <MyWithinEpsController:MyWithinEpsController/>
  
   <xsl:variable name="vMyWithinEpsController" select="document('')/*/MyWithinEpsController:*[1]"/>
  
  <xsl:template name="within">
	 <xsl:param name="pGenerator" select="/.."/>
	 <xsl:param name="pParam0" select="/.."/>
	 <xsl:param name="Eps" select="0.1"/>
  
	  <xsl:variable name="vResultList">
		  <xsl:call-template name="buildListWhile">
		    <xsl:with-param name="pGenerator" select="$pGenerator"/>
		    <xsl:with-param name="pParam0" select="$pParam0"/>
		    <xsl:with-param name="pController" select="$vMyWithinEpsController"/>
	        <xsl:with-param name="pContollerParam" select="$Eps"/>
		  </xsl:call-template>
	  </xsl:variable>
	  
	  <xsl:value-of select="ext:node-set($vResultList)/*[last()]"/>
  </xsl:template>

  <xsl:template name="MyWithinEpsController" match="*[namespace-uri()='MyWithinEpsController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:choose>
         <xsl:when test="count($pList) &lt; 2">1</xsl:when>
	     <xsl:when test="count($pList) >= 2">
	       <xsl:variable name="lastDiff" select="$pList[last()] - $pList[last() - 1]"/>
	       
	       <xsl:if test="not($lastDiff &lt;= $pParams 
	                   and $lastDiff >= (0 - $pParams))">1</xsl:if>
	     </xsl:when>
	     <xsl:otherwise>1</xsl:otherwise>
     </xsl:choose>
  </xsl:template>

</xsl:stylesheet>