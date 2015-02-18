<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:testmap="testmap"
exclude-result-prefixes="xsl testmap"
>
   <xsl:import href="str-map.xsl"/>
   
   <!-- to be applied on any xml source -->
   
   <testmap:testmap/>

   <xsl:output omit-xml-declaration="yes" indent="yes"/>
   
   <xsl:template match="/">
     <xsl:variable name="vTestMap" select="document('')/*/testmap:*[1]"/>
     <xsl:call-template name="str-map">
       <xsl:with-param name="pFun" select="$vTestMap"/>
       <xsl:with-param name="pStr" select="'0123456789'"/>
     </xsl:call-template>
   </xsl:template>

    <xsl:template name="double" match="*[namespace-uri() = 'testmap']">
      <xsl:param name="arg1"/>
      
      <xsl:value-of select="2 * $arg1"/>
    </xsl:template>

</xsl:stylesheet>