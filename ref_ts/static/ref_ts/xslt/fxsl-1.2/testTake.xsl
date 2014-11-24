<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:pGenerator="pGenerator"
xmlns:DropWhileController="DropWhileController"
xmlns:MyRepeatGenerator="MyRepeatGenerator" 
xmlns:MyRepeatableFunction="MyRepeatableFunction"
exclude-result-prefixes="xsl ext pGenerator DropWhileController 
                         MyRepeatGenerator MyRepeatableFunction"
>

  <xsl:import href="take.xsl"/> 
  <xsl:import href="drop.xsl"/>
  <xsl:import href="dropWhile.xsl"/>
  
  <!-- To be applied on any xml source. -->

  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <pGenerator:pGenerator/>
  <DropWhileController:DropWhileController/>
  <MyRepeatGenerator:MyRepeatGenerator/>
  <MyRepeatableFunction:MyRepeatableFunction/>
  
   <xsl:variable name="vMyGenerator" select="document('')/*/pGenerator:*[1]"/>
   <xsl:variable name="vDropWhileController" select="document('')/*/DropWhileController:*[1]"/>
   <xsl:variable name="vMyRepeat" select="document('')/*/MyRepeatGenerator:*[1]"/>
   <xsl:variable name="vMyFunction" select="document('')/*/MyRepeatableFunction:*[1]"/>
  
  <xsl:template match="/">

    <xsl:variable name="vTake8">
	    <xsl:call-template name="take">
	      <xsl:with-param name="pGenerator" select="$vMyGenerator"/>
		  <xsl:with-param name="pN" select="8"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:copy-of select="ext:node-set($vTake8)/*"/>
   
    <xsl:text>&#xA;</xsl:text>
    <xsl:text>&#xA;</xsl:text>
      
    <xsl:call-template name="take">
      <xsl:with-param name="pList" select="ext:node-set($vTake8)/*"/>
	  <xsl:with-param name="pN" select="3"/>
    </xsl:call-template>

    <xsl:text>&#xA;</xsl:text>
    <xsl:text>&#xA;</xsl:text>
  
    <xsl:call-template name="drop">
      <xsl:with-param name="pList" select="ext:node-set($vTake8)/*"/>
	  <xsl:with-param name="pN" select="3"/>
    </xsl:call-template>

    <xsl:text>&#xA;</xsl:text>
    <xsl:text>&#xA;</xsl:text>
   
    <xsl:call-template name="dropWhile">
	    <xsl:with-param name="pList" select="ext:node-set($vTake8)/*"/>
	    <xsl:with-param name="pController" select="$vDropWhileController"/>
	</xsl:call-template>


    <xsl:text>&#xA;</xsl:text>
    <xsl:text>&#xA;</xsl:text>
  <xsl:call-template name="take">
    <xsl:with-param name="pN" select="10"/>
    <xsl:with-param name="pGenerator" select="$vMyRepeat"/>
    <xsl:with-param name="pParam0" select="5"/>
    <xsl:with-param name="pParamGenerator" select="$vMyFunction"/>
  </xsl:call-template>



  </xsl:template>
  
  <xsl:template name="listGenerator" match="*[namespace-uri()='pGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:value-of select="(count($pList) + 1) * 2"/>
  </xsl:template>
   
   <xsl:template name="myDWController" match="*[namespace-uri()='DropWhileController']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     
     <xsl:if test="$pList &lt;= 10">1</xsl:if>
  </xsl:template>
 
  <xsl:template name="myRepeater" match="*[namespace-uri()='MyRepeatGenerator']">
     <xsl:param name="pList" select="/.."/>
     <xsl:param name="pParams"/>
     <xsl:param name="pParamGenerator" select="/.."/>
     
     <xsl:choose>
	     <xsl:when test="not($pList)">
	        <xsl:copy-of select="$pParams"/>
	     </xsl:when>
	     <xsl:otherwise>
	       <xsl:apply-templates select="$pParamGenerator[1]">
	         <xsl:with-param name="X" select="$pList[last()]"/>
	         <xsl:with-param name="N" select="9"/>
	       </xsl:apply-templates>
	     </xsl:otherwise>
     </xsl:choose>
  </xsl:template>

  <xsl:template name="myRptFn" match="*[namespace-uri()='MyRepeatableFunction']">
     <xsl:param name="X"/>
     <xsl:param name="N"/>
     
     <xsl:value-of select="($X + ($N div $X)) div 2"/>
  </xsl:template>
  


</xsl:stylesheet>