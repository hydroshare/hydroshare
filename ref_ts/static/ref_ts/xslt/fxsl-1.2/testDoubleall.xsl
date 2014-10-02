<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
   <xsl:import href="doubleall.xsl"/>

   <!-- This transformation must be applied to:
        numList.xml 
    -->
   
   <xsl:output omit-xml-declaration="yes"/>
   
   <xsl:template match="/">
     <xsl:call-template name="doubleall">
       <xsl:with-param name="pList" select="/*/*"/>
     </xsl:call-template>
   </xsl:template>
</xsl:stylesheet>