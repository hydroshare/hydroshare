<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 exclude-result-prefixes="ext"
>

   <xsl:import href="strSplit-to-Words.xsl"/>
<!-- This transformation must be applied to:
        testSplitToWords3.xml               
-->

   <xsl:output indent="yes" omit-xml-declaration="yes"/>
   
    <xsl:template match="/">
      <xsl:variable name="vwordNodes">
        <xsl:call-template name="str-split-to-words">
          <xsl:with-param name="pStr" select="/root/para"/>
          <xsl:with-param name="pDelimiters" 
                          select="'&#10;&#13;'"/>
        </xsl:call-template>
      </xsl:variable>
      
      <root>
        <xsl:apply-templates 
             select="ext:node-set($vwordNodes)/*"/>
      </root>
    </xsl:template>
    
    <xsl:template match="word">
      <xsl:if test="string(.)">
        <para>
          <xsl:value-of select="."/>
       </para>
      </xsl:if>
    </xsl:template>
</xsl:stylesheet>