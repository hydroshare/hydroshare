<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
   <xsl:import href="tree-labels-list.xsl"/>
   
   <!-- This transformation must be applied to:
        numTree.xml 
    -->

    <xsl:output indent="yes" omit-xml-declaration="yes"/>
    
    <xsl:template match="/">
      <xsl:call-template name="tree-labels-list">
        <xsl:with-param name="pTree" select="/*"/>
      </xsl:call-template>
    </xsl:template>
    
</xsl:stylesheet>