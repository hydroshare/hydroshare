<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:myFunction="myFunction" 
exclude-result-prefixes="xsl myFunction"
>
  <xsl:import href="easyDiffList.xsl"/>
  
  <!-- To be applied on any xml. This produces the derivative of
       x^2 for x = 15, with precision 0.000001
   -->

  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <myFunction:myFunction/>
  
  <xsl:template match="/">
    <xsl:variable name="vMyFun" select="document('')/*/myFunction:*[1]"/>
    
    <xsl:call-template name="easyDiffList">
	    <xsl:with-param name="pFun" select="$vMyFun"/>
	    <xsl:with-param name="pX" select="15"/>
	    <xsl:with-param name="pH0" select="0.1"/>
	    <xsl:with-param name="pEps" select="0.000001"/>
    </xsl:call-template>
  
  </xsl:template>

  <xsl:template name="myFunction" match="*[namespace-uri()='myFunction']">
     <xsl:param name="pParam" select="/.."/>
     
     <xsl:value-of select="$pParam * $pParam"/>
  </xsl:template>

</xsl:stylesheet>