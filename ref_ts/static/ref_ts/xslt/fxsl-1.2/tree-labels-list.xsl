<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:tree-labels-append="tree-labels-append"
xmlns:tree-labels-cons="tree-labels-cons" 
exclude-result-prefixes="xsl tree-labels-append tree-labels-cons"
>
    <xsl:import href="foldl-tree.xsl"/>
    <xsl:import href="append.xsl"/>

    <tree-labels-append:tree-labels-append/>
    <tree-labels-cons:tree-labels-cons/>
    
    <xsl:template name="tree-labels-list">
      <xsl:param name="pTree"/>
      
      <xsl:variable name="vAppend" select="document('')/*/tree-labels-append:*[1]"/>
      <xsl:variable name="vCons" select="document('')/*/tree-labels-cons:*[1]"/>
      
      <xsl:call-template name="foldl-tree">
	    <xsl:with-param name="pFuncNode" select="$vCons"/>
	    <xsl:with-param name="pFuncSubtrees" select="$vAppend"/>
	    <xsl:with-param name="pA0" select="/.."/>
	    <xsl:with-param name="pNode" select="$pTree"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="*[namespace-uri()='tree-labels-cons']">
      <xsl:param name="arg1"/>
      <xsl:param name="arg2"/>
      
      <el><xsl:value-of select="$arg1"/></el>
      <xsl:copy-of select="$arg2"/>
    </xsl:template>
    
    <xsl:template match="*[namespace-uri()='tree-labels-append']">
      <xsl:param name="arg1"/>
      <xsl:param name="arg2"/>
      
      <xsl:call-template name="append">
        <xsl:with-param name="pList1" select="$arg1"/>
        <xsl:with-param name="pList2" select="$arg2"/>
      </xsl:call-template>
    </xsl:template>

</xsl:stylesheet>