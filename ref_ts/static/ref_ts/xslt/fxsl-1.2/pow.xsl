<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:myMultiply="f:myMultiply" 
 exclude-result-prefixes="xsl ext"
 >
 
  <xsl:import href="curry.xsl"/> 
  <xsl:import href="iter.xsl"/>

  <myMultiply:myMultiply/>
 
  <!-- This template implements the following general power fn:
  
	> power :: (Ord a, Num a, Num b) => a -> b -> b
	> power n x = iter n (multByX x) 1
	
	where
	> multByX :: Num a => a -> a -> a
	> multByX x y = (*x) y
	
	Note the use of the partial application in multByX !
    
    -->
  
  <xsl:template name="pow">
    <xsl:param name="pTimes" select="0"/>
    <xsl:param name="pX"/>
    
    <xsl:variable name="vMultiply" select="document('')/*/myMultiply:*[1]"/>
    
    <xsl:variable name="vrtfCurriedMultByX">
	  <xsl:call-template name="curry">
	    <xsl:with-param name="pFun" select="$vMultiply"/>
	    <xsl:with-param name="pNargs" select="2"/>
      <xsl:with-param name="arg2" select="$pX"/>
	  </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vCurriedMultByX" 
                  select="ext:node-set($vrtfCurriedMultByX)/node()"/>
    
    <xsl:call-template name="iter">
      <xsl:with-param name="pTimes" select="$pTimes"/>
      <xsl:with-param name="pFun" select="$vCurriedMultByX"/>
      <xsl:with-param name="pX" select="1"/>
    </xsl:call-template>
    
  </xsl:template>

  
  <xsl:template match="myMultiply:*">
    <xsl:param name="arg1"/>
    <xsl:param name="arg2"/>
  
    <xsl:value-of select="$arg1 * $arg2"/>
  </xsl:template>

</xsl:stylesheet>