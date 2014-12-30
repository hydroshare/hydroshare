<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
>
  <xsl:import href="sqrt.xsl"/>
  
  <!-- To be applied on any source xml. 
       This also tests the within() function 
  -->
  
  <xsl:output indent="yes" omit-xml-declaration="yes"/>
  
  <xsl:template match="/">
     sqrt(0.25): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="0.25"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(1): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="1"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(2): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="2"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(9): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="9"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(16): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="16"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     sqrt(25): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="25"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     sqrt(36): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="36"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(49): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="49"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(64): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="64"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(81): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="81"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(100): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="100"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
     
     sqrt(121): 
     <xsl:call-template name="sqrt">
	    <xsl:with-param name="N" select="121"/>
	    <xsl:with-param name="Eps" select="0.00001"/>
     </xsl:call-template>
  </xsl:template>

</xsl:stylesheet>