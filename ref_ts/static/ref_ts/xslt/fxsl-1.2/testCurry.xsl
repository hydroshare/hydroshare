<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:myMultiply="f:myMultiply"
 exclude-result-prefixes="ext myMultiply "
 >
 
 <xsl:import href="curry.xsl"/>
 
  <xsl:output omit-xml-declaration="yes" indent="yes"/>
 
  <myMultiply:myMultiply/>     <!-- My multiply x y function -->

  <xsl:template match="/">
    <xsl:variable name="vMyMultiply"
                  select="document('')/*/myMultiply:*[1]"/>
    
    <!-- Get the curried fn here -->
    <!-- Get the partial application (*5) -->
    <xsl:variable name="vrtfCurriedMultBy5"> 
      <xsl:call-template name="curry">
        <xsl:with-param name="pFun" select="$vMyMultiply"/>
        <xsl:with-param name="pNargs" select="2"/>
        <xsl:with-param name="arg1" select="5"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vMultBy5"
                  select="ext:node-set($vrtfCurriedMultBy5)/*"/>


    <xsl:apply-templates select="$vMultBy5"> <!-- Apply (*5) on 2 -->
      <xsl:with-param name="arg2" select="2"/>
    </xsl:apply-templates> <!-- The result must be 10 -->

  </xsl:template>
  
  <xsl:template match="myMultiply:*">
    <xsl:param name="arg1"/>
    <xsl:param name="arg2"/>
    
    <xsl:value-of select="$arg1 * $arg2"/>
  </xsl:template>

</xsl:stylesheet>