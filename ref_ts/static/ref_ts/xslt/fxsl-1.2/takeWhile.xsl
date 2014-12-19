<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

  <xsl:import href="buildListWhile.xsl"/>

  <xsl:template name="takeWhile">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pController" select="/.."/>
    <xsl:param name="pContollerParam" select="/.."/>
    <xsl:param name="pGenerator" select="/.."/>
    <xsl:param name="pParam0" select="/.."/>
    <xsl:param name="pParamGenerator" select="/.."/>
    <xsl:param name="pElementName" select="'el'"/>

    <xsl:if test="not($pController)">
      <xsl:message terminate="yes">[takeWhile]Error: pController not specified.</xsl:message>
    </xsl:if>   
    
    <xsl:choose>
      <xsl:when test="$pList">
	    <xsl:variable name="vAccept">
	      <xsl:apply-templates select="$pController">
	        <xsl:with-param name="pList" select="$pList[1]"/>
	        <xsl:with-param name="pParams" select="$pContollerParam"/>
	      </xsl:apply-templates>
	    </xsl:variable>
	    
	    <xsl:if test="string($vAccept)">
		   <xsl:copy-of select="$pList[1]"/>
	       <xsl:call-template name="takeWhile">
			  <xsl:with-param name="pList" select="$pList[position() > 1]" />
			  <xsl:with-param name="pController" select="$pController"/>
			  <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
			  <xsl:with-param name="pGenerator" select="$pGenerator"/>
			  <xsl:with-param name="pParam0" select="$pParam0"/>
			  <xsl:with-param name="pParamGenerator" select="$pParamGenerator"/>
			  <xsl:with-param name="pElementName" select="$pElementName"/>
	       </xsl:call-template>
	    </xsl:if>
      
      </xsl:when>
      <xsl:when test="$pGenerator">
		  <xsl:call-template name="buildListWhile">
			    <xsl:with-param name="pList" select="/.."/>
			    <xsl:with-param name="pGenerator" select="$pGenerator"/>
			    <xsl:with-param name="pController" select="$pController"/>
			    <xsl:with-param name="pContollerParam" select="$pContollerParam"/>
			    <xsl:with-param name="pParam0" select="$pParam0"/>
			    <xsl:with-param name="pParamGenerator" select="$pParamGenerator"/>
			    <xsl:with-param name="pElementName" select="$pElementName"/>
		  </xsl:call-template>
      </xsl:when>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>