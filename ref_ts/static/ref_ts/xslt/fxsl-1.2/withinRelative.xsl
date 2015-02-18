<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:MyWithinRelEpsController="MyWithinRelEpsController"
exclude-result-prefixes="xsl ext MyWithinRelEpsController" 
>

  <xsl:import href="buildListWhile.xsl"/>

  <MyWithinRelEpsController:MyWithinRelEpsController/>
  
   <xsl:variable name="vMyWithinRelEpsController" select="document('')/*/MyWithinRelEpsController:*[1]"/>
  
  <xsl:template name="withinRelative">
	 <xsl:param name="pGenerator" select="/.."/>
	 <xsl:param name="pParam0" select="/.."/>
	 <xsl:param name="Eps" select="0.1"/>
  
	  <xsl:variable name="vResultList">
		  <xsl:call-template name="buildListWhile">
		    <xsl:with-param name="pGenerator" select="$pGenerator"/>
		    <xsl:with-param name="pParam0" select="$pParam0"/>
		    <xsl:with-param name="pController" select="$vMyWithinRelEpsController"/>
	        <xsl:with-param name="pContollerParam" select="$Eps"/>
		  </xsl:call-template>
	  </xsl:variable>
	  
	  <xsl:value-of select="ext:node-set($vResultList)/*[last()]"/>
  </xsl:template>

  <xsl:template name="MyWithinRelEpsController" match="*[namespace-uri()='MyWithinRelEpsController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:choose>
         <xsl:when test="count($pList) &lt; 2">1</xsl:when>
	     <xsl:when test="count($pList) >= 2">
	       <xsl:variable name="lastDiff" select="$pList[last()] - $pList[last() - 1]"/>
	       <xsl:variable name="lastProd" select="$pParams * $pList[last()]"/>
	       
	       <xsl:if test="not($lastDiff &lt;= $lastProd 
	                   and $lastDiff >= (0 - $lastProd))">1</xsl:if>
	     </xsl:when>
	     <xsl:otherwise>1</xsl:otherwise>
     </xsl:choose>
  </xsl:template>

</xsl:stylesheet>