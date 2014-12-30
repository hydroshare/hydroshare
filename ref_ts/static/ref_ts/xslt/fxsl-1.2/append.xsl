<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:append-foldr-func="append-foldr-func"
exclude-result-prefixes="xsl append-foldr-func"
>
   <xsl:import href="foldr.xsl"/>

   <append-foldr-func:append-foldr-func/>

    <xsl:template name="append">
      <xsl:param name="pList1" select="/.."/>
      <xsl:param name="pList2" select="/.."/>

      <xsl:variable name="vFoldrFun" select="document('')/*/append-foldr-func:*[1]"/>

      <xsl:call-template name="foldr">
        <xsl:with-param name="pFunc" select="$vFoldrFun"/>
        <xsl:with-param name="pList" select="$pList1"/>
        <xsl:with-param name="pA0" select="$pList2"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template name="appendL" match="*[namespace-uri() = 'append-foldr-func']">
         <xsl:param name="arg1" select="/.."/>
         <xsl:param name="arg2" select="/.."/>
         
         <xsl:copy-of select="$arg1"/>
         <xsl:copy-of select="$arg2"/>
    </xsl:template>

</xsl:stylesheet>