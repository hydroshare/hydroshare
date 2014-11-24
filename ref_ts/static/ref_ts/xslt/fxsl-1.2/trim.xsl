<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:myTrimDropController="f:myTrimDropController" 
xmlns:myTrim1="f:myTrim1" 
xmlns:myReverse="f:myReverse" 
exclude-result-prefixes="xsl ext myTrimDropController myTrim1 myReverse"
>
  <xsl:import href="str-dropWhile.xsl"/>
  <xsl:import href="compose-flist.xsl"/>
  <xsl:import href="reverse.xsl"/>
  
  <myTrimDropController:myTrimDropController/>
  
  <xsl:template name="trim">
    <xsl:param name="pStr"/>
    
    <xsl:variable name="vrtfParam">
      <myReverse:myReverse/>
      <myTrim1:myTrim1/>
      <myReverse:myReverse/>
      <myTrim1:myTrim1/>
    </xsl:variable>

    <xsl:call-template name="compose-flist">
        <xsl:with-param name="pFunList" select="ext:node-set($vrtfParam)/*"/>
        <xsl:with-param name="pArg1" select="$pStr"/>
    </xsl:call-template>
    
  </xsl:template>
  
  <xsl:template name="trim1" match="myTrim1:*">
    <xsl:param name="pArg1"/>
    
  <xsl:variable name="vTab" select="'&#9;'"/>
  <xsl:variable name="vNL" select="'&#10;'"/>
  <xsl:variable name="vCR" select="'&#13;'"/>
  <xsl:variable name="vWhitespace" 
                select="concat(' ', $vTab, $vNL, $vCR)"/>

    <xsl:variable name="vFunController" 
                  select="document('')/*/myTrimDropController:*[1]"/>
           
    
    <xsl:call-template name="str-dropWhile">
      <xsl:with-param name="pStr" select="$pArg1"/>
      <xsl:with-param name="pController" select="$vFunController"/>
      <xsl:with-param name="pContollerParam" select="$vWhitespace"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="myTrimDropController:*">
    <xsl:param name="pChar"/>
    <xsl:param name="pParams"/>
    
    <xsl:if test="contains($pParams, $pChar)">1</xsl:if>
  </xsl:template>
  
  <xsl:template name="myReverse" match="myReverse:*">
    <xsl:param name="pArg1"/>
    
    <xsl:call-template name="strReverse">
      <xsl:with-param name="pStr" select="$pArg1"/>
    </xsl:call-template>
</xsl:template>
</xsl:stylesheet>