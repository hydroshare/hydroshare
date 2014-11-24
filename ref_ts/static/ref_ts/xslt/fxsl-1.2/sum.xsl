<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:sum-fold-func="sum-fold-func"
exclude-result-prefixes="xsl sum-fold-func"
>
   <xsl:import href="foldl.xsl"/>

   <sum-fold-func:sum-fold-func/>

    <xsl:template name="sum">
      <xsl:param name="pList" select="/.."/>

      <xsl:variable name="sum-fold-func:vFoldFun" select="document('')/*/sum-fold-func:*[1]"/>
      
      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$sum-fold-func:vFoldFun"/>
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pA0" select="0"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template name="add" match="*[namespace-uri() = 'sum-fold-func']">
         <xsl:param name="arg1" select="0"/>
         <xsl:param name="arg2" select="0"/>
         
         <xsl:value-of select="$arg1 + $arg2"/>
    </xsl:template>


</xsl:stylesheet>