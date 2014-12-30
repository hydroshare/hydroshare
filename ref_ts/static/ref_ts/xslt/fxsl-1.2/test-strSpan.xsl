<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:myController="f:myController"
 xmlns:x="f:myTest"
 >
  <xsl:import href="strSpan.xsl"/>
  <!-- To be applied on csstext.xml -->
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
  
  <myController:myController/>
  
  <xsl:variable name="x:st" select="document('')/*"/>
  
  <xsl:template match="/">
    <xsl:call-template name="strSpan">
      <xsl:with-param name="pStr" select="string(/*)"/>
      <xsl:with-param name="pController" 
                      select="$x:st/myController:*[1]"/>
      <xsl:with-param name="pContollerParam" 
                      select="'0123456789.'"/>
      <xsl:with-param name="pElementName1" select="'value'"/>
      <xsl:with-param name="pElementName2" select="'unit'"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="myController:*">
    <xsl:param name="pChar"/>
    <xsl:param name="pParams"/>
    
    <xsl:if test="contains($pParams, $pChar)">1</xsl:if>
  </xsl:template>
</xsl:stylesheet>