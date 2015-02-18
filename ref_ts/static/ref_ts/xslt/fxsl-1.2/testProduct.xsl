<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
   <xsl:import href="product.xsl"/>

    <xsl:output  encoding="UTF-8" omit-xml-declaration="yes"/>

   <!-- This transformation must be applied to:
        numList.xml 
     -->

    <xsl:template match="/">

      <xsl:call-template name="product">
        <xsl:with-param name="pList" select="/*/*"/>
      </xsl:call-template>
    </xsl:template>


</xsl:stylesheet>

