<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

  <xsl:template name="filter">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pListName" select="'list'"/>
    
    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[filter]Error: pController not specified.</xsl:message>
    </xsl:if>
    
    <xsl:element name="{$pListName}">
      <xsl:call-template name="_filter">
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pController" select="$pController"/>
      </xsl:call-template>
    </xsl:element>

  </xsl:template>    

  <xsl:template name="_filter">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pController" select="/.."/>

    <xsl:if test="$pList">
      <xsl:variable name="vthisNode" select="$pList[1]"/>
		  
		  <xsl:variable name="vHolds">
		    <xsl:apply-templates select="$pController">
		      <xsl:with-param name="arg1" select="$vthisNode"/>
		    </xsl:apply-templates>
		  </xsl:variable>
	    
	    <xsl:if test="string($vHolds)">
	      <xsl:copy-of select="$vthisNode"/>
	    </xsl:if>
	    
	    <xsl:call-template name="_filter">
	      <xsl:with-param name="pList" select="$pList[position() > 1]"/>
	      <xsl:with-param name="pController" select="$pController"/>
	    </xsl:call-template>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>