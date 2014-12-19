<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:myHalve="myHalve" 
xmlns:myTenXController="myTenXController" 
xmlns:myEasyDiffMap="myEasyDiffMap"
xmlns:myWithinController="myWithinController"
exclude-result-prefixes="xsl ext myHalve myTenXController
 myEasyDiffMap myWithinController"
>
  <xsl:import href="buildListWhileMap.xsl"/>
  <myHalve:myHalve/>
  <myWithinController:myWithinController/>
  <myTenXController:myTenXController/>
  <myEasyDiffMap:myEasyDiffMap/>
  
  <xsl:template name="easyDiffList">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pX"/>
    <xsl:param name="pH0" select="0.1"/>
    <xsl:param name="pEps" select="0.01"/>
    
    <xsl:variable name="vMyHalveGenerator" select="document('')/*/myHalve:*[1]"/>
    <xsl:variable name="vmyWithinController" select="document('')/*/myWithinController:*[1]"/>
    <xsl:variable name="vmyTenXController" select="document('')/*/myTenXController:*[1]"/>
    <xsl:variable name="vmyEasyDiffMap" select="document('')/*/myEasyDiffMap:*[1]"/>
  
    <xsl:variable name="fx">
      <xsl:apply-templates select="$pFun">
        <xsl:with-param name="pParam" select="$pX"/>
      </xsl:apply-templates>
    </xsl:variable>
    
    <xsl:variable name="vrtfMapParams">
      <xsl:copy-of select="$pFun"/>
      <param><xsl:value-of select="$pX"/></param>
      <param><xsl:value-of select="$fx"/></param>
    </xsl:variable>
    
    <xsl:variable name="vMapParams" select="ext:node-set($vrtfMapParams)/*"/>
    
    <xsl:call-template name="buildListWhileMap">
	    <xsl:with-param name="pGenerator" select="$vMyHalveGenerator"/>
	    <xsl:with-param name="pParam0" select="$pH0"/>
	    <xsl:with-param name="pController" select="$vmyWithinController"/>
	    <xsl:with-param name="pContollerParam" select="$pEps"/>
	    <xsl:with-param name="pMap" select="$vmyEasyDiffMap"/>
	    <xsl:with-param name="pMapParams" select="$vMapParams"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="myHalveGenerator" match="*[namespace-uri()='myHalve']">
     <xsl:param name="pParams" select="/.."/>
     <xsl:param name="pList" select="/.."/>
     
     <xsl:choose>
       <xsl:when test="not($pList)"><xsl:value-of select="$pParams"/></xsl:when>
       <xsl:otherwise><xsl:value-of select="$pList[last()] div 2"/></xsl:otherwise>
     </xsl:choose>
  </xsl:template>
  
  <xsl:template name="myWithinController" match="*[namespace-uri()='myWithinController']">
     <xsl:param name="pParams" select="/.."/>
     <xsl:param name="pList" select="/.."/>
     
     <xsl:variable name="vLastDiff" select="$pList[last()] - $pList[last() - 1]"/>
     
     
     <xsl:choose>
       <xsl:when test="not($vLastDiff &lt; $pParams 
                      and $vLastDiff > (0 - $pParams))
                      and count($pList) &lt;= 40
                      ">1</xsl:when>
     </xsl:choose>
  </xsl:template>

  <xsl:template name="myEasyDiffMap" match="*[namespace-uri()='myEasyDiffMap']">
     <xsl:param name="pParams" select="/.."/>
     <xsl:param name="pDynParams" select="/.."/>
     <xsl:param name="pList" select="/.."/>
     
     <xsl:variable name="x" select="$pParams[2]"/>
     <xsl:variable name="h" select="$pDynParams[1]"/>
     
     
     <xsl:choose>
	     <xsl:when test="not($h = 0)">
		     <xsl:variable name="fx_plus_h">
			     <xsl:apply-templates select="$pParams[1]">
			       <xsl:with-param name="pParam" select="$x + $h"/>
			     </xsl:apply-templates>
		     </xsl:variable>
		     
		     <xsl:variable name="fx">
		         <xsl:choose>
			         <xsl:when test="count($pParams) >= 3">
			           <xsl:value-of select="$pParams[3]"/>
			         </xsl:when>
			         <xsl:otherwise>
					     <xsl:apply-templates select="$pParams[1]">
					       <xsl:with-param name="pParam" select="$x"/>
					     </xsl:apply-templates>
				     </xsl:otherwise>
			     </xsl:choose>
		     </xsl:variable>
		     
		     <xsl:value-of select="($fx_plus_h - $fx) div $h"/>
	     </xsl:when>
	     <xsl:otherwise><xsl:value-of select="$pList[last()]"/></xsl:otherwise>
     </xsl:choose>
  </xsl:template>
</xsl:stylesheet>