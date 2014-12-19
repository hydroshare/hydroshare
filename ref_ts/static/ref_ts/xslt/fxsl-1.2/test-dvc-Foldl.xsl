<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:dvc-foldl-func="dvc-foldl-func"
exclude-result-prefixes="xsl dvc-foldl-func"
>

   <xsl:import href="dvc-foldl.xsl"/>

   <dvc-foldl-func:dvc-foldl-func/>
   <xsl:variable name="vFoldlFun" select="document('')/*/dvc-foldl-func:*[1]"/>
    <xsl:output  encoding="UTF-8" omit-xml-declaration="yes"/>

    <xsl:template match="/">

      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$vFoldlFun"/>
        <xsl:with-param name="pList" select="/*/*"/>
        <xsl:with-param name="pA0" select="0"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="dvc-foldl-func:*">
         <xsl:param name="arg1" select="0"/>
         <xsl:param name="arg2" select="0"/>
         
         <xsl:value-of select="$arg1 + $arg2"/>
    </xsl:template>

</xsl:stylesheet>