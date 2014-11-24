<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:func-transform2="f:func-transform2"
exclude-result-prefixes="xsl func-transform2"
>
   <xsl:import href="transform-and-sum.xsl"/>
   <xsl:import href="hex-to-decimal.xsl"/>

   <!-- to be applied on testTransform-and-sum2.xml -->
   
   <xsl:output method="text"/>
   
   <func-transform2:func-transform2/>

    <xsl:template match="/">
      <xsl:call-template name="transform-and-sum">
        <xsl:with-param name="pFuncTransform" 
                        select="document('')/*/func-transform2:*[1]"/>
        <xsl:with-param name="pList" select="/*/*"/>
      </xsl:call-template>
    </xsl:template>
    
    <xsl:template match="func-transform2:*">
      <xsl:param name="arg" select="0"/>
      
      <xsl:call-template name="hex-to-decimal">
        <xsl:with-param name="pxNumber" select="$arg"/>
      </xsl:call-template>
    </xsl:template>

</xsl:stylesheet>