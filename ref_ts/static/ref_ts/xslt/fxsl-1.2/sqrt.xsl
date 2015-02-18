<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:MyRepeatGenerator="MyRepeatGenerator" 
xmlns:MyRepeatableFunction="MyRepeatableFunction"
exclude-result-prefixes="xsl ext MyRepeatGenerator MyRepeatableFunction" 
>

  <xsl:import href="within.xsl"/>
  <!-- <xsl:import href="withinRelative.xsl"/> -->

  <MyRepeatGenerator:MyRepeatGenerator/>
  <MyRepeatableFunction:MyRepeatableFunction/>
  
   <xsl:variable name="vMyRepeat" select="document('')/*/MyRepeatGenerator:*[1]"/>
   <xsl:variable name="vMyFunction" select="document('')/*/MyRepeatableFunction:*[1]"/>
   
  <xsl:template name="sqrt">
    <xsl:param name="N"/>
    <xsl:param name="Eps" select="0.1"/>
    
    <xsl:variable name="vrtfParams">
      <param><xsl:value-of select="$N div 2"/></param>
      <xsl:copy-of select="$vMyFunction"/>
      <param><xsl:value-of select="$N"/></param>
    </xsl:variable>

    <xsl:call-template name="within">
      <xsl:with-param name="pGenerator" select="$vMyRepeat"/>
      <xsl:with-param name="pParam0" select="ext:node-set($vrtfParams)/*"/>
	  <xsl:with-param name="Eps" select="$Eps"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="myRepeater" match="*[namespace-uri()='MyRepeatGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:choose>
	     <xsl:when test="not($pList)">
	        <xsl:copy-of select="$pParams[1]/node()"/>
	     </xsl:when>
	     <xsl:otherwise>
	       <xsl:apply-templates select="$pParams[2]">
	         <xsl:with-param name="X" select="$pList[last()]"/>
	         <xsl:with-param name="N" select="$pParams[3]/node()"/>
	       </xsl:apply-templates>
	     </xsl:otherwise>
     </xsl:choose>
  </xsl:template>

  <xsl:template name="myRptFn" match="*[namespace-uri()='MyRepeatableFunction']">
     <xsl:param name="X"/>
     <xsl:param name="N"/>
     
     <xsl:value-of select="($X + ($N div $X)) div 2"/>
  </xsl:template>

</xsl:stylesheet>