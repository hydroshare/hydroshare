<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
>

   <xsl:import href="strSplit-to-Words.xsl"/>
   <xsl:import href="sum.xsl"/>

   <xsl:output indent="yes" omit-xml-declaration="yes"/>
   
    <xsl:template match="/">
      <xsl:variable name="vwordNodes">
        <xsl:call-template name="str-split-to-words">
          <xsl:with-param name="pStr" select="/"/>
          <xsl:with-param name="pDelimiters" 
                          select="', &#9;&#10;&#13;'"/>
        </xsl:call-template>
      </xsl:variable>
      
      <xsl:call-template name="sum">
        <xsl:with-param name="pList" 
             select="ext:node-set($vwordNodes)/*[. != '']"/>
      </xsl:call-template>
    </xsl:template>
    
    <xsl:template match="word">
      <xsl:value-of select="concat(position(), ' ', ., '&#10;')"/>
    </xsl:template>

</xsl:stylesheet>