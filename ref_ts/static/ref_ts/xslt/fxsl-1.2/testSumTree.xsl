<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
    <xsl:import href="sumTree.xsl"/>

   <!-- This transformation must be applied to:
        numTree.xml 
    -->

    <xsl:output method="text"/>
    
    <xsl:template match="/">
      <xsl:call-template name="sumTree">
        <xsl:with-param name="pTree" select="/*"/>
      </xsl:call-template>
    </xsl:template>

</xsl:stylesheet>