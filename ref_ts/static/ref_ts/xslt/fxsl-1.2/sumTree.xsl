<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:add-tree="add-tree" 
exclude-result-prefixes="xsl add-tree"
>
    <xsl:import href="foldl-tree.xsl"/>

    <add-tree:add-tree/>
    
    <xsl:template name="sumTree">
      <xsl:param name="pTree"/>
      
      <xsl:variable name="vAdd" select="document('')/*/add-tree:*[1]"/>
      
      <xsl:call-template name="foldl-tree">
	    <xsl:with-param name="pFuncNode" select="$vAdd"/>
	    <xsl:with-param name="pFuncSubtrees" select="$vAdd"/>
	    <xsl:with-param name="pA0" select="0"/>
	    <xsl:with-param name="pNode" select="$pTree"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="*[namespace-uri()='add-tree']">
      <xsl:param name="arg1"/>
      <xsl:param name="arg2"/>
      
      <xsl:value-of select="$arg1 + $arg2"/>
    </xsl:template>

</xsl:stylesheet>