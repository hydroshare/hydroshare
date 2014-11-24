<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:prod-fold-func="prod-fold-func"
exclude-result-prefixes="xsl prod-fold-func"
>
   <xsl:import href="foldl.xsl"/>

   <prod-fold-func:prod-fold-func/>

    <xsl:template name="product">
      <xsl:param name="pList" select="/.."/>

      <xsl:variable name="prod-fold-func:vFoldFun" select="document('')/*/prod-fold-func:*[1]"/>
      
      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$prod-fold-func:vFoldFun"/>
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pA0" select="1"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template name="multiply" match="*[namespace-uri() = 'prod-fold-func']">
         <xsl:param name="arg1" select="0"/>
         <xsl:param name="arg2" select="0"/>
         
         <xsl:value-of select="$arg1 * $arg2"/>
    </xsl:template>


</xsl:stylesheet>