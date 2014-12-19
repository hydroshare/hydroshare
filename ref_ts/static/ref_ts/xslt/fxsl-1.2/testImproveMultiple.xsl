<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:myImproveGenerator="myImproveGenerator"
xmlns:myImproveController="myImproveController"
>
  <xsl:import href="improve.xsl"/>
  <xsl:import href="take.xsl"/> 
  <xsl:import href="takeWhile.xsl"/> 
  
  <myImproveGenerator:myImproveGenerator/>
  <myImproveController:myImproveController/>

  <!-- To be applied on diff-results.xml -->

  <xsl:output indent="yes" omit-xml-declaration="yes"/>
 
  <xsl:template match="/">
     <xsl:variable name="vMyImproveGenerator" select="document('')/*/myImproveGenerator:*[1]"/>
     <xsl:variable name="vMyImproveController" select="document('')/*/myImproveController:*[1]"/>

    <xsl:variable name="vrtfResults">
	    <xsl:call-template name="takeWhile">
	      <xsl:with-param name="pGenerator" select="$vMyImproveGenerator"/>
		  <xsl:with-param name="pParam0" select="/*/*"/>
		  <xsl:with-param name="pController" select="$vMyImproveController"/>
	      <xsl:with-param name="pContollerParam" select="0.00000000000001"/>
		</xsl:call-template>
	</xsl:variable>
	
	<xsl:copy-of select="ext:node-set($vrtfResults)/*"/>
	
  </xsl:template>
  
  <xsl:template name="myImproveGenerator" match="*[namespace-uri()='myImproveGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams" select="/.."/>
     
     <xsl:choose>
       <xsl:when test="not($pList)">
         <xsl:call-template name="improve">
	        <xsl:with-param name="pList" select="$pParams"/>
         </xsl:call-template>
       </xsl:when>
       <xsl:otherwise>
         <xsl:call-template name="improve">
	        <xsl:with-param name="pList" select="$pList[last()]/*"/>
         </xsl:call-template>
       </xsl:otherwise>
     </xsl:choose>

  </xsl:template>
  
  <xsl:template name="MyImproveController" match="*[namespace-uri()='myImproveController']">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pParams" select="0.01"/>
    
    <xsl:choose>
      <xsl:when test="count($pList) &lt; 2">1</xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vDiff" select="$pList[last()]/*[2] 
                                          - $pList[last() - 1]/*[2]"/>
        <xsl:if test="not($vDiff &lt; $pParams 
                     and $vDiff > (0 - $pParams))
                     and count($pList) &lt;= 5
                     ">1</xsl:if>
      </xsl:otherwise>
    </xsl:choose>
  
  </xsl:template>
</xsl:stylesheet>