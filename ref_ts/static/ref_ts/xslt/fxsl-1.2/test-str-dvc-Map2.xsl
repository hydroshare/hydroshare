<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:testmap="testmap"
exclude-result-prefixes="xsl testmap"
>
   <xsl:import href="str-dvc-map.xsl"/>
   
   <testmap:testmap/>

   <xsl:output omit-xml-declaration="yes" indent="yes"/>
   
   <xsl:template match="/">
     <xsl:variable name="vTestMap" select="document('')/*/testmap:*[1]"/>
     <xsl:call-template name="str-dvc-map">
       <xsl:with-param name="pFun" select="$vTestMap"/>
       <xsl:with-param name="pStr" select="string(/*)"/>
     </xsl:call-template>
   </xsl:template>

    <xsl:template name="indentNL" match="*[namespace-uri() = 'testmap']">
      <xsl:param name="arg1"/>
      
      <xsl:value-of select="$arg1"/>
      <xsl:if test="$arg1='&#10;'">
        <xsl:value-of select="'    '"/>
      </xsl:if>
    </xsl:template>

</xsl:stylesheet>