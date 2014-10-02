<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:mapTree-cons="mapTree-cons" 
 xmlns:mapTree-makeNode-f="mapTree-makeNode-f" 
 exclude-result-prefixes="xsl ext mapTree-cons mapTree-makeNode-f"
>
    <xsl:import href="foldl-tree.xsl"/>

    <mapTree-cons:mapTree-cons/>
    <mapTree-makeNode-f:mapTree-makeNode-f/>
    
    <xsl:template name="mapTree">
      <xsl:param name="pTree"/>
      <xsl:param name="pFun"/>
      
      <xsl:variable name="vmakeNode" select="document('')/*/mapTree-makeNode-f:*[1]"/>
      <xsl:variable name="vCons" select="document('')/*/mapTree-cons:*[1]"/>
      
      <xsl:variable name="vFuncNode">
        <mapTree-makeNode-f:mapTree-makeNode-f/>
        <xsl:copy-of select="$pFun"/>
      </xsl:variable>
      
      <xsl:call-template name="foldl-tree">
	    <xsl:with-param name="pFuncNode" select="ext:node-set($vFuncNode)/*"/>
	    <xsl:with-param name="pFuncSubtrees" select="$vCons"/>
	    <xsl:with-param name="pA0" select="/.."/>
	    <xsl:with-param name="pNode" select="$pTree"/>
      </xsl:call-template>
    </xsl:template>

    <xsl:template match="*[namespace-uri()='mapTree-cons']">
      <xsl:param name="arg1"/>
      <xsl:param name="arg2"/>
      
      <xsl:copy-of select="$arg1"/>
      <xsl:copy-of select="$arg2"/>
    </xsl:template>
    
    <xsl:template match="*[namespace-uri()='mapTree-makeNode-f']">
      <xsl:param name="arg0"/> <!-- must contain pFun -->
      <xsl:param name="arg1"/> <!-- must contain the node -->
      <xsl:param name="arg2"/> <!-- must contan pA0 -->
      
      <xsl:variable name="vFun1Result">
         <xsl:apply-templates select="$arg0[1]">
           <xsl:with-param name="arg1" select="$arg1"/>
         </xsl:apply-templates>
      </xsl:variable>

      <xsl:element name="{name($arg1/..)}">
      <xsl:apply-templates select="$arg1" mode="copy">
        <xsl:with-param name="pContents" select="ext:node-set($vFun1Result)"/>
      </xsl:apply-templates>
      <xsl:copy-of select="$arg1/../node()[not(self::*)]"/>
      <xsl:copy-of select="$arg2"/>
      </xsl:element>
    </xsl:template>

    <xsl:template match="node()" mode="copy">
      <xsl:param name="pContents"/>
      
      <xsl:copy>
        <xsl:copy-of select="$pContents"/>
      </xsl:copy>
    </xsl:template>

    <xsl:template match="@*" mode="copy">
      <xsl:param name="pContents"/>
      
      <xsl:attribute name="{name()}">
        <xsl:copy-of select="$pContents"/>
      </xsl:attribute>
    </xsl:template>

</xsl:stylesheet>