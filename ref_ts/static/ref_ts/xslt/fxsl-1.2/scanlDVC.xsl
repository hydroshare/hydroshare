<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
exclude-result-prefixes="xsl ext"
>
  <xsl:template name="scanl">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pQ0" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pElName" select="'el'"/>
    <xsl:param name="pStarting" select="1"/>
    
    <xsl:variable name="vLength" select="count($pList)"/>

    <xsl:choose>
      <xsl:when test="$vLength > 1">
        <xsl:variable name="vHalf" select="floor($vLength div 2)"/>
          
        <xsl:variable name="vrtfResult1">
		      <xsl:call-template name="scanl">
				    <xsl:with-param name="pFun" select="$pFun"/>
				    <xsl:with-param name="pQ0" select="$pQ0" />
				    <xsl:with-param name="pList" select="$pList[position() &lt;= $vHalf]"/>
				    <xsl:with-param name="pElName" select="$pElName"/>
            <xsl:with-param name="pStarting" select="$pStarting"/>
		      </xsl:call-template>
	      </xsl:variable>
	      
	      <xsl:variable name="vResult1" select="ext:node-set($vrtfResult1)/*"/>
	      
	      <xsl:copy-of select="$vResult1"/>
	      
	      <xsl:call-template name="scanl">
			    <xsl:with-param name="pFun" select="$pFun"/>
			    <xsl:with-param name="pQ0" select="$vResult1[last()]" />
			    <xsl:with-param name="pList" select="$pList[position() > $vHalf]"/>
			    <xsl:with-param name="pElName" select="$pElName"/>
          <xsl:with-param name="pStarting" select="0"/>
	      </xsl:call-template>
      </xsl:when>

      <xsl:otherwise>
		    <xsl:if test="$pStarting">
			    <xsl:element name="{$pElName}">
			      <xsl:copy-of select="ext:node-set($pQ0)/node()"/>
			    </xsl:element>
		    </xsl:if>
    
        <xsl:if test="$pList">
			    <xsl:element name="{$pElName}">
			      <xsl:apply-templates select="$pFun">
			        <xsl:with-param name="pArg1" select="$pQ0"/>
			        <xsl:with-param name="pArg2" select="$pList[1]"/>
			      </xsl:apply-templates>
			    </xsl:element>
        </xsl:if>
      </xsl:otherwise>
    </xsl:choose>
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