<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
   <xsl:import href="product.xsl"/>
   
   <!-- To be applied on: salesMap.xml -->

     <xsl:output  encoding="UTF-8" omit-xml-declaration="yes"/>

    <xsl:template match="/">

      <xsl:call-template name="product">
        <xsl:with-param name="pList" select="/sales/sale[1]/*"/>
      </xsl:call-template>
    </xsl:template>


</xsl:stylesheet>
