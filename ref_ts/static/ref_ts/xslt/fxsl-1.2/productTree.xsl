<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:mult-tree="mult-tree" 
exclude-result-prefixes="xsl mult-tree"
>
    <xsl:import href="foldl-tree.xsl"/>

    <mult-tree:mult-tree/>
    
    <xsl:template name="productTree">
      <xsl:param name="pTree"/>
      
      <xsl:variable name="vMult" select="document('')/*/mult-tree:*[1]"/>
      
      <xsl:call-template name="foldl-tree">
	    <xsl:with-param name="pFuncNode" select="$vMult"/>
	    <xsl:with-param name="pFuncSubtrees" select="$vMult"/>
	    <xsl:with-param name="pA0" select="1"/>
	    <xsl:with-param name="pNode" select="$pTree"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="*[namespace-uri()='mult-tree']">
      <xsl:param name="arg1"/>
      <xsl:param name="arg2"/>
      
      <xsl:value-of select="$arg1 * $arg2"/>
    </xsl:template>

</xsl:stylesheet>