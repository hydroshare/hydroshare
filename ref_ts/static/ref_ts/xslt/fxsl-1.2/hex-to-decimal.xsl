<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:hex-converter="f:hex-converter"
>
  <xsl:import href="str-foldl.xsl"/>
  
  <hex-converter:hex-converter/>
  
  <xsl:variable name="hexDigits" select="'0123456789ABCDEF'"/>
  
  <xsl:template name="hex-to-decimal">
    <xsl:param name="pxNumber"/>
    
    <xsl:variable name="vFunXConvert" 
                  select="document('')/*/hex-converter:*[1]"/>
    
    <xsl:call-template name="str-foldl">
      <xsl:with-param name="pFunc" select="$vFunXConvert"/>
      <xsl:with-param name="pA0" select="0"/>
      <xsl:with-param name="pStr" select="$pxNumber"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="hex-converter:*">
    <xsl:param name="arg1"/> <!-- $pA0 -->
    <xsl:param name="arg2"/> <!-- a char (digit) -->
    
    <xsl:value-of select="16 * $arg1 
                        + string-length(substring-before($hexDigits, $arg2))"/>
  </xsl:template>
</xsl:stylesheet>

