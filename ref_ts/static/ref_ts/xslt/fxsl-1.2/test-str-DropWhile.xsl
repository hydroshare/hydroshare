<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myDropController="f:mymyDropController" 
exclude-result-prefixes="xsl myDropController"
>
  <xsl:import href="str-dropWhile.xsl"/>
  
  <xsl:output method="text"/>
  <myDropController:myDropController/>
  
  <xsl:variable name="vTab" select="'&#9;'"/>
  <xsl:variable name="vNL" select="'&#10;'"/>
  <xsl:variable name="vCR" select="'&#13;'"/>
  <xsl:variable name="vWhitespace" 
                select="concat(' ', $vTab, $vNL, $vCR)"/>
  
  <xsl:template match="/">
    <xsl:variable name="vFunController" 
                  select="document('')/*/myDropController:*[1]"/>
           
    
    '<xsl:call-template name="str-dropWhile">
      <xsl:with-param name="pStr" select="concat('  ', $vTab, $vCR, $vNL,
                                                 'Some   Text',
                                                 $vNL, $vTab, '   ',$vCR
                                                 )"/>
      <xsl:with-param name="pController" select="$vFunController"/>
      <xsl:with-param name="pContollerParam" select="$vWhitespace"/>
    </xsl:call-template>'
  </xsl:template>
  
  <xsl:template match="myDropController:*">
    <xsl:param name="pChar"/>
    <xsl:param name="pParams"/>
    
    <xsl:if test="contains($pParams, $pChar)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>

