<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
exclude-result-prefixes="xsl ext"
>
  <xsl:template name="buildListUntil">
    <xsl:param name="pGenerator" select="/.."/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pParam0" select="/.."/>
    <xsl:param name="pParamGenerator" select="/.."/>
    <xsl:param name="pElementName" select="'el'"/>
    <xsl:param name="pList" select="/.."/>

    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">
      [buildListUntil]Error: No pController specified:
         would cause infinite processing.
      </xsl:message>
    </xsl:if>   
    
    <xsl:variable name="vElement">
      <xsl:element name="{$pElementName}">
      <xsl:apply-templates select="$pGenerator">
        <xsl:with-param name="pParams" select="$pParam0"/>
        <xsl:with-param name="pList" select="$pList"/>
      </xsl:apply-templates>
      </xsl:element>
    </xsl:variable>
    
    <xsl:variable name="newList">
      <xsl:copy-of select="$pList"/>
      <xsl:copy-of select="ext:node-set($vElement)/*"/>
    </xsl:variable>
    
    <xsl:variable name="vResultList" select="ext:node-set($newList)/*"/>
    
    <xsl:variable name="vShouldStop">
      <xsl:apply-templates select="$pController">
        <xsl:with-param name="pList" select="$vResultList"/>
        <xsl:with-param name="pParams" select="$pParam0"/>
      </xsl:apply-templates>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="string($vShouldStop)">
        <xsl:copy-of select="$vResultList"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vNewParams">
          <xsl:apply-templates select="$pParamGenerator">
	        <xsl:with-param name="pList" select="$vResultList"/>
	        <xsl:with-param name="pParams" select="$pParam0"/>
          </xsl:apply-templates>
        </xsl:variable>
        
        <xsl:call-template name="buildListUntil">
		    <xsl:with-param name="pGenerator" select="$pGenerator"/>
		    <xsl:with-param name="pController" select="$pController"/>
		    <xsl:with-param name="pParam0" select="ext:node-set($vNewParams)/*"/>
		    <xsl:with-param name="pParamGenerator" select="$pParamGenerator"/>
		    <xsl:with-param name="pElementName" select="$pElementName"/>
		    <xsl:with-param name="pList" select="$vResultList" />
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>