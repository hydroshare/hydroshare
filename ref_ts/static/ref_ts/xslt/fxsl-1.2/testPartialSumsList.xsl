<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:IntegralFunction="IntegralFunction"
exclude-result-prefixes="xsl IntegralFunction"
>
  <xsl:import href="partialSumsList.xsl"/>

  <!-- To be applied on any source xml.
       Calculates the partial sums for 
       the Integral of x^2 in the interval [0,1] 
       with precision 0.001
    -->
  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <IntegralFunction:IntegralFunction/>

  <xsl:template match="/">
    <xsl:variable name="vMyFun" select="document('')/*/IntegralFunction:*[1]"/>

    <xsl:variable name="vrtfPartialSums">
      <xsl:call-template name="partialSumsList">
          <xsl:with-param name="pFun" select="$vMyFun"/>
          <xsl:with-param name="pA" select="0"/>
          <xsl:with-param name="pB" select="1"/>
          <xsl:with-param name="pEps" select="0.001"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vPartialSums" select="ext:node-set($vrtfPartialSums)/*"/>
    
    <xsl:copy-of select="$vPartialSums"/>
    

  </xsl:template>
  <xsl:template name="myIntegralFn" match="*[namespace-uri()='IntegralFunction']">
    <xsl:param name="pX"/>

    <xsl:value-of select="$pX * $pX"/>
  </xsl:template>

</xsl:stylesheet>