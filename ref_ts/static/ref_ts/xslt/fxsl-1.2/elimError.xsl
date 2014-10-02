<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>

  <xsl:import href="exp.xsl"/>

  <xsl:variable name="vLn-2" select="0.69314718056"/>  
  <xsl:template name="elimError">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pOrder" select="-9999999"/>
    <xsl:param name="pv2__N" select="0"/>
    
    <xsl:choose>
      <xsl:when test="count($pList) &lt; 3">
        <xsl:copy-of select="$pList"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vOrder">
	        <xsl:choose>
	          <xsl:when test="$pOrder &lt; -9999998">
	            <xsl:call-template name="getOrder">
	              <xsl:with-param name="pList" select="$pList"/>
	            </xsl:call-template>
	          </xsl:when>
	          <xsl:otherwise>
	            <xsl:value-of select="$pOrder"/>
	          </xsl:otherwise>
	        </xsl:choose>
        </xsl:variable> 
      
        <xsl:variable name="v2__N">
          <xsl:choose>
	          <xsl:when test="$pv2__N = 0">
		          <xsl:call-template name="pow">
			        <xsl:with-param name="base" select="2"/>
			        <xsl:with-param name="pow" select="$vOrder"/>
		          </xsl:call-template>
	          </xsl:when>
	          <xsl:otherwise>
		          <xsl:value-of select="$pv2__N"/>
	          </xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        
        <xsl:element name="{name($pList[1])}">
          <xsl:value-of select="($pList[2] * $v2__N - $pList[1]) 
                                 div 
                                  ($v2__N - 1)"/>
        </xsl:element>
        
        <xsl:variable name="vNewList" select="$pList[position() > 1]"/>
        
        <xsl:variable name="vNewOrder">
            <xsl:call-template name="getOrder">
              <xsl:with-param name="pList" select="$vNewList"/>
            </xsl:call-template>
        </xsl:variable> 
        <xsl:call-template name="elimError">
		    <xsl:with-param name="pList" select="$vNewList"/>
		    <xsl:with-param name="pOrder" select="$vNewOrder"/>
		    <xsl:with-param name="pv2__N" select="$v2__N"/>
        </xsl:call-template>
        
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="getOrder">
    <xsl:param name="pList" select="/.."/>
    
    <xsl:choose>
      <xsl:when test="count($pList) &lt; 3">1</xsl:when>
      <xsl:otherwise>
        <xsl:variable name="v1">
          <xsl:choose>
            <xsl:when test="not($pList[2] = $pList[3])">
              <xsl:value-of select="($pList[1] - $pList[3])
                                    div 
                                     ($pList[2] - $pList[3])
                                      - 1"/>
            </xsl:when>
            <xsl:otherwise>0</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        
        <xsl:variable name="v2">
          <xsl:choose>
            <xsl:when test="$v1 > 0">
              <xsl:value-of select="$v1"/>
            </xsl:when>
            <xsl:when test="$v1 &lt; 0">
              <xsl:value-of select="(-1) * $v1"/>          
            </xsl:when>
            <xsl:otherwise>1</xsl:otherwise>
          </xsl:choose>
        </xsl:variable>
        
        <xsl:call-template name="roundLog2">
          <xsl:with-param name="pX" select="number($v2)"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="roundLog2">
    <xsl:param name="pX"/>
    
    <xsl:variable name="vLog2-X">
      <xsl:call-template name="log2">
        <xsl:with-param name="pX" select="$pX"/>
      </xsl:call-template>
    </xsl:variable>
    
<!--    <xsl:value-of select="math:round(math:log($pX) div $vLn-2)"/> -->

    <xsl:variable name="vFloor" select="floor($vLog2-X)"/>
    <xsl:variable name="vCeil" select="ceiling($vLog2-X)"/>
    
    <xsl:choose>
      <xsl:when test="$vLog2-X - $vFloor > $vCeil - $vLog2-X">
        <xsl:value-of select="$vCeil"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$vFloor"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
   <xsl:template name="pow">
        <xsl:param name="base" select="1"/>
        <xsl:param name="pow" select="0"/>
        <xsl:param name="tmpResult" select="1"/>

        <xsl:variable name="result">
            <xsl:choose>
                <xsl:when test="$pow >= 0">
                    <xsl:value-of select="$tmpResult * $base"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="$tmpResult div $base"/>
                </xsl:otherwise>
           </xsl:choose>
        </xsl:variable>

        <xsl:variable name="incr">
            <xsl:choose>
                <xsl:when test="$pow >= 0">
                    <xsl:value-of select="- 1"/>
                </xsl:when>
                <xsl:otherwise>
                    <xsl:value-of select="1"/>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:variable>

        <xsl:choose>
            <xsl:when test="$pow = 0">
                <xsl:value-of select="$tmpResult"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:call-template name="pow">
                    <xsl:with-param name="base" select="$base"/>
                    <xsl:with-param name="pow" select="$pow + $incr"/>
                    <xsl:with-param name="tmpResult" select="$result"/>
                </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
  
</xsl:stylesheet>