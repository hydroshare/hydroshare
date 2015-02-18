<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:pGenerator="pGenerator"
xmlns:pController="pController"
xmlns:IntervalParams="IntervalParams"
xmlns:mapEasyIntegrate="mapEasyIntegrate"
xmlns:easy-integrate="easy-integrate"
exclude-result-prefixes="xsl ext pGenerator pController IntervalParams easy-integrate"
>
  <xsl:import href="buildListWhileMap.xsl"/>
  <xsl:import href="foldl.xsl"/>

  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <pGenerator:pGenerator/>
  <pController:pController/>
  <mapEasyIntegrate:mapEasyIntegrate/>
  <easy-integrate:easy-integrate/>


  <xsl:template name="partialSumsList">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pA"/>
    <xsl:param name="pB"/>
    <xsl:param name="pEps" select="0.001"/>

  <xsl:variable name="vMyGenerator" select="document('')/*/pGenerator:*[1]"/>
  <xsl:variable name="vMyController" select="document('')/*/pController:*[1]"/>
  <xsl:variable name="vmyEasyIntegrateMap" select="document('')/*/mapEasyIntegrate:*[1]"/>

    <xsl:variable name="vrtfvIntervalParams">
      <IntervalParams:IntervalParams>
        <Interval>
          <el><xsl:value-of select="$pA"/></el>
          <el><xsl:value-of select="$pB"/></el>
        </Interval>
        <xsl:copy-of select="$pFun"/>
      </IntervalParams:IntervalParams>
    </xsl:variable>

    <xsl:variable name="vIntervalParams" select="ext:node-set($vrtfvIntervalParams)/*"/>


    <xsl:variable name="vrtfResultIntervalList">
      <xsl:call-template name="buildListWhileMap">
        <xsl:with-param name="pGenerator" select="$vMyGenerator"/>
        <xsl:with-param name="pController" select="$vMyController"/>
        <xsl:with-param name="pParam0" select="$vIntervalParams"/>
        <xsl:with-param name="pContollerParam" select="$pEps"/>
	    <xsl:with-param name="pMap" select="$vmyEasyIntegrateMap"/>
	  </xsl:call-template>
    </xsl:variable>

    <xsl:copy-of select="ext:node-set($vrtfResultIntervalList)"/>

    <xsl:variable name="vResultIntervalList"
       select="ext:node-set($vrtfResultIntervalList)/*[last()]/*"/>

  </xsl:template>

  <xsl:template name="listGenerator" match="*[namespace-uri()='pGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>

     <xsl:variable name="pA0" select="string($pParams/*[1]/*[1])"/>
     <xsl:variable name="pB0" select="string($pParams/*[1]/*[2])"/>
     <xsl:variable name="pFun" select="$pParams/*[2]"/>

     <xsl:choose>
       <xsl:when test="not($pList)">
         <xsl:variable name="vFa">
           <xsl:apply-templates select="$pFun">
             <xsl:with-param name="pX" select="$pA0"/>
           </xsl:apply-templates>
         </xsl:variable>

         <xsl:variable name="vFb">
           <xsl:apply-templates select="$pFun">
             <xsl:with-param name="pX" select="$pB0"/>
           </xsl:apply-templates>
         </xsl:variable>

         <e><xsl:value-of select="$pB0 - $pA0"/></e>
         <e><xsl:value-of select="$vFa"/></e>
         <e><xsl:value-of select="$vFb"/></e>
       </xsl:when>
       <xsl:otherwise>
          <xsl:variable name="vprevH" select="$pList[last()]/*[1]"/>
          <xsl:variable name="vH" select="$vprevH div 2"/>
          <e><xsl:value-of select="$vH"/></e>
          <xsl:for-each select="$pList[last()]/*[position() > 1
                                             and position() != last()]">
           <xsl:variable name="vA" select="$pA0 + (position() - 1) * $vprevH"/>

           <xsl:variable name="vMid" select="$vA + $vH"/>

           <xsl:variable name="vF_mid">
             <xsl:apply-templates select="$pFun">
               <xsl:with-param name="pX" select="$vMid"/>
             </xsl:apply-templates>
           </xsl:variable>

           <xsl:copy-of select="."/>
           <e><xsl:value-of select="$vF_mid"/></e>
         </xsl:for-each>
         <xsl:copy-of select="$pList[last()]/*[last()]"/>
       </xsl:otherwise>
     </xsl:choose>

  </xsl:template>

  <xsl:template name="listController" match="*[namespace-uri()='pController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>

     <xsl:choose>
         <xsl:when test="count($pList) &lt; 2">1</xsl:when>
         <xsl:otherwise>
             <xsl:variable name="vLastDiff" select="$pList[last()]
                                                  - $pList[last() - 1]"/>

             <xsl:if test="not($vLastDiff &lt; $pParams
                       and $vLastDiff > (0 - $pParams))">1</xsl:if>
         </xsl:otherwise>
     </xsl:choose>
  </xsl:template>

  <xsl:template name="mapEasyIntegrate" match="*[namespace-uri()='mapEasyIntegrate']">
     <xsl:param name="pParams" select="/.."/> <!-- pMapParams -->
     <xsl:param name="pDynParams" select="/.."/> <!-- NewBaseListElement -->
     <xsl:param name="pList" select="/.."/>

     <xsl:variable name="vResult">
     	<xsl:call-template name="multiIntegrate">
	      <xsl:with-param name="pList" select="$pDynParams/*"/>
	    </xsl:call-template>
	 </xsl:variable>

	 <xsl:copy-of select="ext:node-set($vResult)"/>
  </xsl:template>

  <xsl:template name="multiIntegrate">
    <xsl:param name="pList" select="/*/*"/>

    <xsl:variable name="vmyeasyIntegrateFn" select="document('')/*/easy-integrate:*[1]"/>

      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$vmyeasyIntegrateFn"/>
        <xsl:with-param name="pList" select="$pList[position() > 1
                                              and position() &lt; last()]"/>
        <xsl:with-param name="pA0" select="0"/>
      </xsl:call-template>

  </xsl:template>

  <xsl:template name="myEasyIntegrateFn" match="*[namespace-uri()='easy-integrate']">
    <xsl:param name="arg1" select="0"/> <!-- pA0 -->
    <xsl:param name="arg2" select="0"/> <!-- node -->

    <xsl:value-of
       select="$arg1
             +
               (($arg2 + $arg2/following-sibling::*[1])
                 div 2
                ) * $arg2/../*[1]"/>

  </xsl:template>

</xsl:stylesheet>