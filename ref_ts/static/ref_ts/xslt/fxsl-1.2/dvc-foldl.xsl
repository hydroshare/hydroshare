<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:ext="http://exslt.org/common"
  exclude-result-prefixes="ext"
>
    <xsl:template name="foldl">
      <xsl:param name="pFunc" select="/.."/>
      <xsl:param name="pA0"/>
      <xsl:param name="pList" select="/.."/>

      <xsl:choose>
         <xsl:when test="not($pList)">
            <xsl:copy-of select="$pA0"/>
         </xsl:when>
         <xsl:otherwise>
            <xsl:variable name="vcntList" select="count($pList)"/>
            <xsl:choose>
              <xsl:when test="$vcntList = 1">
                  <xsl:apply-templates select="$pFunc[1]">
                    <xsl:with-param name="arg0" select="$pFunc[position() > 1]"/>
                    <xsl:with-param name="arg1" select="$pA0"/>
                    <xsl:with-param name="arg2" select="$pList[1]"/>
                  </xsl:apply-templates>
              </xsl:when>
              <xsl:otherwise>
                <xsl:variable name="vHalfLen"
                              select="floor($vcntList div 2)"/>
                <xsl:variable name="vFunResult1">
                  <xsl:call-template name="foldl">
                    <xsl:with-param name="pFunc" select="$pFunc"/>
                    <xsl:with-param name="pA0" select="$pA0"/>
                    <xsl:with-param name="pList"
                                    select="$pList[position()
                                                 &lt;=
                                                   $vHalfLen
                                                   ]"/>
                  </xsl:call-template>
                </xsl:variable>

                <xsl:call-template name="foldl">
    		        <xsl:with-param name="pFunc" select="$pFunc"/>
    		        <xsl:with-param name="pList" select="$pList[position() > $vHalfLen]"/>
    		        <xsl:with-param name="pA0" select="ext:node-set($vFunResult1)/node()"/>

                </xsl:call-template>
              </xsl:otherwise>
            </xsl:choose>
         </xsl:otherwise>
      </xsl:choose>

    </xsl:template>

</xsl:stylesheet>