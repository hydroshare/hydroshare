<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:x="f:fxsl-test-monteCarlo"
 xmlns:mySampleFun1="f:mySampleFun1"
 xmlns:mySampleFun2="f:mySampleFun2"
 xmlns:mySampleFun3="f:mySampleFun3"
 exclude-result-prefixes="xsl mySampleFun1"
 >
 
  <xsl:import href="monteCarlo.xsl"/>
  
  <xsl:output method="text"/>
  
  <mySampleFun1:mySampleFun1/>
  <mySampleFun2:mySampleFun2/>
  <mySampleFun3:mySampleFun3/>

  <xsl:variable name="x:st" 
                select="document('')/*"/>

  <xsl:template match="/">
    <xsl:variable name="vSampleFun1" 
                  select="$x:st/mySampleFun1:*[1]"/>
    <xsl:variable name="vSampleFun2" 
                  select="$x:st/mySampleFun2:*[1]"/>
    <xsl:variable name="vSampleFun3" 
                  select="$x:st/mySampleFun3:*[1]"/>
    
    <xsl:call-template name="monteCarlo">
      <xsl:with-param name="arg1" select="10000"/>
      <xsl:with-param name="arg2" 
                      select="$vSampleFun1"/>
      <xsl:with-param name="arg3" 
                      select="'0'"/> <!-- sx -->
      <xsl:with-param name="arg4" 
                      select="1"/>   <!-- tx -->
      <xsl:with-param name="arg5" 
                      select="'0'"/> <!-- sy -->
      <xsl:with-param name="arg6" 
                      select="4"/>   <!-- ty -->
    </xsl:call-template>
    <xsl:text>&#xA;</xsl:text>
    <xsl:call-template name="monteCarlo">
      <xsl:with-param name="arg1" select="10000"/>
      <xsl:with-param name="arg2" 
                      select="$vSampleFun2"/>
      <xsl:with-param name="arg3" 
                      select="'0'"/> <!-- sx -->
      <xsl:with-param name="arg4" 
                      select="1"/>   <!-- tx -->
      <xsl:with-param name="arg5" 
                      select="'0'"/> <!-- sy -->
      <xsl:with-param name="arg6" 
                      select="1"/>   <!-- ty -->
    </xsl:call-template>
    <xsl:text>&#xA;</xsl:text>
    <xsl:call-template name="monteCarlo">
      <xsl:with-param name="arg1" select="10000"/>
      <xsl:with-param name="arg2" 
                      select="$vSampleFun3"/>
      <xsl:with-param name="arg3" 
                      select="1"/> <!-- sx -->
      <xsl:with-param name="arg4" 
                      select="2"/>   <!-- tx -->
      <xsl:with-param name="arg5" 
                      select="'0'"/> <!-- sy -->
      <xsl:with-param name="arg6" 
                      select="1"/>   <!-- ty -->
    </xsl:call-template>
  </xsl:template>
  
  <!-- f x = 4 / (1 + x^2) -->
  <xsl:template match="mySampleFun1:*"> 
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="4 
                       div (1 + $arg1*$arg1)"/>
  </xsl:template>

  <!-- f x = x -->
  <xsl:template match="mySampleFun2:*"> 
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="$arg1"/>
  </xsl:template>

  <!-- f x = 1 / x -->
  <xsl:template match="mySampleFun3:*"> 
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="1 div $arg1"/>
  </xsl:template>
</xsl:stylesheet>