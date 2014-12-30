<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:mySquare="f:mySquare" 
 xmlns:myDouble="f:myDouble"
 exclude-result-prefixes="xsl ext mySquare myDouble"
 >
  
  <xsl:import href="randomList.xsl"/>
  
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
   <!-- This transformation must be applied to:
        numList.xml                            
     -->
  
  <mySquare:mySquare/>
  <myDouble:myDouble/>
  
  <xsl:template match="/">
  
    <xsl:variable name="vrtfRands">
      <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="100"/>
      </xsl:call-template>
    </xsl:variable>
    
    Random Recursive Index (dScale (randomSequence 100)):
    
    <xsl:call-template name="_dScale">
      <xsl:with-param name="pRandSeq" 
          select="ext:node-set($vrtfRands)/*"/>
    </xsl:call-template>
    
    Random Recursive Index 10:
    
    <xsl:variable name="vrtfRecIndex">
      <xsl:call-template name="_randomRecursiveIndex">
        <xsl:with-param name="pList" 
        select="/*/*"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vRecIndex" 
              select="ext:node-set($vrtfRecIndex)/*"/>
              
    <xsl:for-each select="$vRecIndex">
      <xsl:copy-of select="."/>&#xA;
    </xsl:for-each>
    
    Randomized 10-elements list:
    <xsl:call-template name="_permutationFromRecursiveIndex">
      <xsl:with-param name="pList" select="/*/*"/>
      <xsl:with-param name="pRecIndex" select="$vRecIndex"/>
    </xsl:call-template>
    
    RandomizeList:
    <xsl:call-template name="randomizeList">
      <xsl:with-param name="pList" select="/*/*"/>
    </xsl:call-template>
    
    <xsl:variable name="vFunSquare" 
         select="document('')/*/mySquare:*[1]"/>
    
    _mapFromRandIndex (^2) [1..10] seed:
    <xsl:call-template name="_mapFromRandIndex">
      <xsl:with-param name="pFun" select="$vFunSquare"/>
      <xsl:with-param name="pList" select="/*/*"/>
      <xsl:with-param name="pRecIndex" select="$vRecIndex"/>
    </xsl:call-template>
    
    <xsl:variable name="vFunDouble" 
         select="document('')/*/myDouble:*[1]"/>
    
    randomMap (*2) [1..10] seed:
    <xsl:call-template name="randomMap">
      <xsl:with-param name="pFun" select="$vFunDouble"/>
      <xsl:with-param name="pList" select="/*/*"/>
    </xsl:call-template>
    
    randListIndex [1..10] seed:
    <xsl:call-template name="randListIndex">
      <xsl:with-param name="pList" select="/*/*"/>
    </xsl:call-template>
    
  </xsl:template>
  
  <xsl:template match="mySquare:*">
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="$arg1 * $arg1"/>
  </xsl:template>

  <xsl:template match="myDouble:*">
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="$arg1 + $arg1"/>
  </xsl:template>
</xsl:stylesheet>