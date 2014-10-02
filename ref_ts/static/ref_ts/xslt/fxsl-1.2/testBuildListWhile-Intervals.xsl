<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:pGenerator="pGenerator"
xmlns:pController="pController"
xmlns:IntervalParams="IntervalParams"
xmlns:IntegralFunction="IntegralFunction"
exclude-result-prefixes="xsl ext pGenerator pController IntervalParams IntegralFunction"
>
  <!-- <xsl:import href="buildListWhile.xsl"/> -->
  <xsl:import href="takeWhile.xsl"/> 
  <xsl:import href="take.xsl"/> 
  
   <!-- to be applied on any xml source -->
   
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <pGenerator:pGenerator/>
  <pController:pController/>

  <IntervalParams:IntervalParams>
    <Interval>
	    <el>0</el>
	    <el>1</el>
    </Interval>
    <IntegralFunction:IntegralFunction/>
  </IntervalParams:IntervalParams>
  
  <xsl:variable name="vMyGenerator" select="document('')/*/pGenerator:*[1]"/>
  <xsl:variable name="vMyController" select="document('')/*/pController:*[1]"/>
  <xsl:variable name="vIntervalParams" select="document('')/*/IntervalParams:*[1]"/>

  <xsl:template match="/">
    <xsl:variable name="vrtfResultIntervalList">
      <xsl:call-template name="buildListWhile">
        <xsl:with-param name="pGenerator" select="$vMyGenerator"/>
        <xsl:with-param name="pController" select="$vMyController"/>
        <xsl:with-param name="pParam0" select="$vIntervalParams"/>
        <xsl:with-param name="pContollerParam" select="256"/>
	  </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vResultIntervalList"
       select="ext:node-set($vrtfResultIntervalList)/*[last()]/*"/>
       
    <xsl:for-each select="$vResultIntervalList">
     <xsl:value-of select="concat(position(), '. ', ., '&#xA;')"/>
    </xsl:for-each>
    
  </xsl:template>

  <xsl:template name="listGenerator" match="*[namespace-uri()='pGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:choose>
       <xsl:when test="not($pList)">
           <xsl:copy-of select="$pParams/*[1]/*"/>
       </xsl:when>
       <xsl:otherwise>
         <xsl:variable name="pFun" select="$pParams/*[2]"/>
          
          <xsl:for-each select="$pList[last()]/*[position() != last()]">
           <xsl:variable name="vFx">
             <xsl:apply-templates select="$pFun">
               <xsl:with-param name="pX" select="string(.)"/>
             </xsl:apply-templates>
           </xsl:variable>
           
           <xsl:variable name="vMid" select="following-sibling::*[1]"/>
           
           <xsl:variable name="vF_mid">
             <xsl:apply-templates select="$pFun">
               <xsl:with-param name="pX" select="string($vMid)"/>
             </xsl:apply-templates>
           </xsl:variable>
           
           
           
           <e><xsl:value-of select="."/></e>
           <e><xsl:value-of select="(. + $vMid) div 2"/></e>
         </xsl:for-each>
         <xsl:copy-of select="$pList[last()]/*[last()]"/>
       </xsl:otherwise>
     </xsl:choose>
     
  </xsl:template>
  
  <xsl:template name="listController" match="*[namespace-uri()='pController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>

     <xsl:if test="count($pList[last()]/*) &lt;= $pParams">1</xsl:if>
  </xsl:template>
  
  <xsl:template name="myIntegralFn" match="*[namespace-uri()='IntegralFunction']">
    <xsl:param name="pX"/>
    
    <xsl:value-of select="$pX"/>
  </xsl:template>
     
</xsl:stylesheet>