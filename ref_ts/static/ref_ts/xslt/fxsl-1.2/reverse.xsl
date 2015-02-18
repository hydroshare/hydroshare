<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:str-reverse-func="f:str-reverse-func"
exclude-result-prefixes="xsl str-reverse-func"
>

   <xsl:import href="str-foldl.xsl"/>

   <str-reverse-func:str-reverse-func/>

    <xsl:template name="strReverse">
      <xsl:param name="pStr"/>

      <xsl:variable name="vReverseFoldlFun" 
                    select="document('')/*/str-reverse-func:*[1]"/>

      <xsl:call-template name="str-foldl">
        <xsl:with-param name="pFunc" select="$vReverseFoldlFun"/>
        <xsl:with-param name="pStr" select="$pStr"/>
        <xsl:with-param name="pA0" select="/.."/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="str-reverse-func:*">
         <xsl:param name="arg1" select="0"/>
         <xsl:param name="arg2" select="0"/>

         <xsl:value-of select="concat($arg2,$arg1)"/>
    </xsl:template>

</xsl:stylesheet>

