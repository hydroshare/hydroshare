<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:import href="elimError.xsl"/>

  <xsl:template name="improve">
     <xsl:param name="pList" select="/.."/>
     
     <xsl:variable name="vOrder">
        <xsl:call-template name="getOrder">
          <xsl:with-param name="pList" select="$pList"/>
        </xsl:call-template>
     </xsl:variable>
     
     <xsl:variable name="v1Order">
       <xsl:choose>
         <xsl:when test="$vOrder = 0">1</xsl:when>
         <xsl:otherwise><xsl:value-of select="$vOrder"/></xsl:otherwise>
       </xsl:choose>
     </xsl:variable>

     <xsl:call-template name="elimError">
		 <xsl:with-param name="pList" select="$pList"/>
		 <xsl:with-param name="pOrder" select="$v1Order"/>
     </xsl:call-template>

  </xsl:template>
</xsl:stylesheet>