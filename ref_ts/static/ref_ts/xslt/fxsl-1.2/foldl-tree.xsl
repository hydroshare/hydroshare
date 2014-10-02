<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
    <xsl:template name="foldl-tree">
      <xsl:param name="pFuncNode" select="/.."/>
      <xsl:param name="pFuncSubtrees" select="/.."/>
      <xsl:param name="pA0"/>
      <xsl:param name="pNode" select="/.."/>

      <xsl:choose>
         <xsl:when test="not($pNode)">
            <xsl:copy-of select="$pA0"/>
         </xsl:when>
         <xsl:otherwise>
         
            <xsl:variable name="vSubtrees" select="$pNode/*"/>
            
            <xsl:variable name="vSubTreeResult">
              <xsl:call-template name="foldl-tree_">
			      <xsl:with-param name="pFuncNode" select="$pFuncNode"/>
			      <xsl:with-param name="pFuncSubtrees" select="$pFuncSubtrees"/>
			      <xsl:with-param name="pA0" select="$pA0"/>
			      <xsl:with-param name="pSubTrees" select="$vSubtrees"/>
              </xsl:call-template>
            </xsl:variable>

            <xsl:apply-templates select="$pFuncNode[1]">
              <xsl:with-param name="arg0" select="$pFuncNode[position() > 1]"/>
              <xsl:with-param name="arg1" select="$pNode/@tree-nodeLabel"/>
              <xsl:with-param name="arg2" select="$vSubTreeResult"/>
            </xsl:apply-templates>

         </xsl:otherwise>
      </xsl:choose>
    </xsl:template>
    
    <xsl:template name="foldl-tree_">
      <xsl:param name="pFuncNode" select="/.."/>
      <xsl:param name="pFuncSubtrees" select="/.."/>
      <xsl:param name="pA0"/>
      <xsl:param name="pSubTrees" select="/.."/>
      
      <xsl:choose>
         <xsl:when test="not($pSubTrees)">
            <xsl:copy-of select="$pA0"/>
         </xsl:when>
         <xsl:otherwise>
	      <xsl:variable name="vSubTree1Result">
	        <xsl:call-template name="foldl-tree">
		      <xsl:with-param name="pFuncNode" select="$pFuncNode"/>
		      <xsl:with-param name="pFuncSubtrees" select="$pFuncSubtrees"/>
		      <xsl:with-param name="pA0" select="$pA0"/>
		      <xsl:with-param name="pNode" select="$pSubTrees[1]"/>
	        </xsl:call-template>
	      </xsl:variable>
	      
	      <xsl:variable name="vRestSubtreesResult">
	        <xsl:call-template name="foldl-tree_">
		      <xsl:with-param name="pFuncNode" select="$pFuncNode"/>
		      <xsl:with-param name="pFuncSubtrees" select="$pFuncSubtrees"/>
		      <xsl:with-param name="pA0" select="$pA0"/>
		      <xsl:with-param name="pSubTrees" select="$pSubTrees[position() > 1]"/>
	        </xsl:call-template>
	      </xsl:variable>
	      
	        <xsl:apply-templates select="$pFuncSubtrees">
              <xsl:with-param name="arg0" select="$pFuncSubtrees[position() > 1]"/>
              <xsl:with-param name="arg1" select="$vSubTree1Result"/>
              <xsl:with-param name="arg2" select="$vRestSubtreesResult"/>
	        </xsl:apply-templates>
        </xsl:otherwise>
      </xsl:choose>    
    </xsl:template>

</xsl:stylesheet>