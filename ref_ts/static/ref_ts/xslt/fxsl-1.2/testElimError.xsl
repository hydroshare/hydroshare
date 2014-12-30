<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:import href="elimError.xsl"/>
  
  <!-- To be applied on diff-results.xml. 
       This improves the list of derivatives of
       x^2 for x = 6
   -->
  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  <xsl:template match="/">
     <xsl:variable name="vList" select="/*/*"/>
     
     <xsl:variable name="vOrder">
        <xsl:call-template name="getOrder">
          <xsl:with-param name="pList" select="$vList"/>
        </xsl:call-template>
     </xsl:variable>
     
     <xsl:call-template name="elimError">
		 <xsl:with-param name="pList" select="$vList"/>
		 <xsl:with-param name="pOrder" select="$vOrder"/>
     </xsl:call-template>
  </xsl:template>
</xsl:stylesheet>