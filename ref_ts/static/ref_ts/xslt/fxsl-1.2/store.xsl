<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:getInitialStore="f:getInitialStore"
xmlns:getValue="f:getValue0"
xmlns:upd-getValue="f:upd-getValue"
xmlns:updateStore="f:updateStore"
>
  
  
  <xsl:template name="getInitialStore" match="getInitialStore:*">
    <store>
      <getInitialStore:getInitialStore/>
      <getValue:getValue/>
      <updateStore:updateStore/>
    </store>
  </xsl:template>
  
  <xsl:template match="getValue:*">
     <xsl:value-of select="0"/>
  </xsl:template>
  
  <xsl:template match="updateStore:*">
    <xsl:param name="pName"/>
    <xsl:param name="pValue"/>
    
    <store>
      <getInitialStore:getInitialStore/>
      <upd-getValue:getValue>
        <store><xsl:copy-of select="../*"/></store>
        <name><xsl:value-of select="$pName"/></name>
        <value><xsl:value-of select="$pValue"/></value>
      </upd-getValue:getValue> 
      <updateStore:updateStore/>
    </store>
  </xsl:template>
  
  <xsl:template match="upd-getValue:*">
    <xsl:param name="pName"/>
    
    <xsl:choose>
      <xsl:when test="$pName = name">
        <xsl:value-of select="value"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="store/*[local-name()='getValue']">
           <xsl:with-param name="pName" select="$pName"/>
        </xsl:apply-templates>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>