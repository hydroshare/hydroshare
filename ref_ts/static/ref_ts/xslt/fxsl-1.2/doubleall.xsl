<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:doubleall="doubleall"
exclude-result-prefixes="xsl doubleall"
>
   <xsl:import href="map.xsl"/>
   
   <doubleall:doubleall/>
   
   <xsl:template name="doubleall">
     <xsl:param name="pList" select="/.."/>
     
     <xsl:variable name="vFunDouble" select="document('')/*/doubleall:*[1]"/>
     
     <xsl:call-template name="map">
       <xsl:with-param name="pFun" select="$vFunDouble"/>
       <xsl:with-param name="pList1" select="$pList"/>
     </xsl:call-template>
   </xsl:template>

    <xsl:template name="double" match="*[namespace-uri() = 'doubleall']">
      <xsl:param name="arg1"/>
      
      <xsl:value-of select="2 * $arg1"/>
    </xsl:template>
</xsl:stylesheet>