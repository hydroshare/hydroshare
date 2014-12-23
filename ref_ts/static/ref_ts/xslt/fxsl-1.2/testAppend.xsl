<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
   <xsl:import href="append.xsl"/>
   <xsl:output  encoding="UTF-8" omit-xml-declaration="yes"/>
   
   <!-- This transformation must be applied to:
        numList.xml 
    -->

    <xsl:template match="/">

      <xsl:call-template name="append">
        <xsl:with-param name="pList1" select="/*/*[position() > 5]"/>
        <xsl:with-param name="pList2" select="/*/*[position() &lt;= 5]"/>
      </xsl:call-template>
    </xsl:template>
</xsl:stylesheet>

