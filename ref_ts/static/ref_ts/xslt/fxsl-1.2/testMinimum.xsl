<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:minimum-own-compare="minimum-own-compare"
xmlns:Mycompare="Mycompare"
exclude-result-prefixes="xsl Mycompare"
>
   <xsl:import href="minimum.xsl"/>
   
   <xsl:output method="text"/>

   <!-- This transformation must be applied to:
        numList.xml 
    -->

   <Mycompare:Mycompare/>

    <xsl:template match="/">
      <xsl:variable name="vCMPFun" select="document('')/*/Mycompare:*[1]"/>

      <xsl:call-template name="minimum">
        <xsl:with-param name="pList" select="/*/*"/>
        <xsl:with-param name="pCMPFun" select="$vCMPFun"/>

      </xsl:call-template>
    </xsl:template>

    <xsl:template name="MyIsSmaller" match="*[namespace-uri() = 'Mycompare']">
         <xsl:param name="arg1"/>
         <xsl:param name="arg2"/>

         <xsl:choose>
          <xsl:when test="$arg1 &gt; $arg2">1</xsl:when>
          <xsl:otherwise>0</xsl:otherwise>
         </xsl:choose>
    </xsl:template>
</xsl:stylesheet>