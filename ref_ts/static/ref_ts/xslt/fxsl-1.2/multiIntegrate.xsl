<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:easy-integrate="easy-integrate"
>
  <xsl:import href="foldl.xsl"/>
  
  <xsl:output method="text"/>
  
  <easy-integrate:easy-integrate/>
  
  <xsl:template name="multiIntegrate">
    <xsl:param name="pList" select="/.."/>
    
    <xsl:variable name="vmyeasyIntegrateFn" select="document('')/*/easy-integrate:*[1]"/>
    
      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$vmyeasyIntegrateFn"/>
        <xsl:with-param name="pList" select="$pList[position() > 1 
                                              and position() &lt; last()]"/>
        <xsl:with-param name="pA0" select="0"/>
      </xsl:call-template>
    
  </xsl:template>
  
  <xsl:template name="myEasyIntegrateFn" match="*[namespace-uri()='easy-integrate']">
    <xsl:param name="arg1" select="0"/> <!-- pA0 -->
    <xsl:param name="arg2" select="0"/> <!-- node -->
    
    <xsl:value-of 
       select="$arg1 
             + 
               (($arg2 + $arg2/following-sibling::*[1]) 
                 div 2
                ) * $arg2/../*[1]"/>
  
  </xsl:template>
</xsl:stylesheet>