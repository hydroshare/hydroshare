<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:import href="allTrue.xsl"/>
  
  <xsl:output omit-xml-declaration="yes"/>

  <!-- This transformation must be applied to:
        boolNodes.xml 
     -->
  
  <xsl:template match="/">
    <xsl:variable name="allTrue">
	    <xsl:call-template name="allTrue">
	      <xsl:with-param name="pList" select="/*/*"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:if test="not(string($allTrue))">
      <xsl:text>Not </xsl:text>
    </xsl:if>
    <xsl:value-of select="'all nodes contents are true in:'"/>
    <xsl:text>&#xA;</xsl:text>
    <xsl:copy-of select="/*/*"/>
  </xsl:template>
</xsl:stylesheet>
