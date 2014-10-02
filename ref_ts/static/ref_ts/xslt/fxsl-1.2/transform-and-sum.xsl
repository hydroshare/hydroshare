<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:sum-fold-func="f:sum-fold-func"
exclude-result-prefixes="xsl ext sum-fold-func"
>
   <xsl:import href="foldl.xsl"/>

   <sum-fold-func:sum-fold-func/>

    <xsl:template name="transform-and-sum">
      <xsl:param name="pFuncTransform" select="/.."/>
      <xsl:param name="pList" select="/.."/>

      <xsl:variable name="vrtfFoldFun">
        <sum-fold-func:sum-fold-func/>
        <xsl:copy-of select="$pFuncTransform"/>
      </xsl:variable>
      
      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="ext:node-set($vrtfFoldFun)/*"/>
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pA0" select="0"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template name="add" match="sum-fold-func:*">
         <xsl:param name="arg0" select="/.."/>
         <xsl:param name="arg1" select="0"/>
         <xsl:param name="arg2" select="0"/>
         
         <xsl:variable name="vPartialCompose">
           <xsl:apply-templates select="$arg0">
             <xsl:with-param name="arg" select="$arg2"/>
           </xsl:apply-templates>
         </xsl:variable>
         
         <xsl:value-of select="$arg1 + $vPartialCompose"/>
    </xsl:template>


</xsl:stylesheet>