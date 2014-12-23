<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myDepthCompare="f:myDepthCompare" 
exclude-result-prefixes="xsl myDepthCompare"
>
   <xsl:import href="maximum.xsl"/>
 <!-- This transformation must be applied to:
        testMaximum3.xml                     
-->  
   <myDepthCompare:myDepthCompare/>
   
   <xsl:output omit-xml-declaration="yes"/>
    <xsl:template match="/">
    
    <xsl:variable name="vFunCompDepth"
         select="document('')/*/myDepthCompare:*[1]"/>
    
      <xsl:call-template name="maximum">
        <xsl:with-param name="pList" select="//folder"/>
        <xsl:with-param name="pCMPFun" select="$vFunCompDepth"/>
      </xsl:call-template>
    </xsl:template>
    
    <xsl:template match="myDepthCompare:*">
      <xsl:param name="arg1" select="/.."/>
      <xsl:param name="arg2" select="/.."/>
      
      <xsl:if test="count($arg1/ancestor::folder) > count($arg2/ancestor::folder)">1</xsl:if>
    </xsl:template>
</xsl:stylesheet>