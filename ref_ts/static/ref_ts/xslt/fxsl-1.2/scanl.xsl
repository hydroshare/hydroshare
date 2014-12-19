<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>
  <xsl:template name="scanl">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pQ0" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pElName" select="'el'"/>
    
    <xsl:element name="{$pElName}">
      <xsl:copy-of select="ext:node-set($pQ0)/node()"/>
    </xsl:element>
    
    <xsl:if test="$pList">
      <xsl:variable name="vFun_Node">
        <xsl:apply-templates select="$pFun">
          <xsl:with-param name="pArg1" select="$pQ0"/>
          <xsl:with-param name="pArg2" select="$pList[1]"/>
        </xsl:apply-templates>
      </xsl:variable>
      
      <xsl:call-template name="scanl">
	    <xsl:with-param name="pFun" select="$pFun"/>
	    <xsl:with-param name="pQ0" select="$vFun_Node" />
	    <xsl:with-param name="pList" select="$pList[position() > 1]"/>
	    <xsl:with-param name="pElName" select="$pElName"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
  
  <xsl:template name="scanl1">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pElName" select="'el'"/>
    
    <xsl:if test="$pList">
      <xsl:call-template name="scanl">
	    <xsl:with-param name="pFun" select="$pFun"/>
	    <xsl:with-param name="pQ0" select="$pList[1]" />
	    <xsl:with-param name="pList" select="$pList[position() > 1]"/>
	    <xsl:with-param name="pElName" select="$pElName"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
</xsl:stylesheet>