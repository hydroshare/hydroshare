<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 >
 <xsl:import href="strSplit-to-Words.xsl"/>
 <xsl:output method="text"/>

 <!-- To be applied on test-strSplit-to-Words8.xml -->

  <xsl:template match="/">
    <xsl:variable name="vrtfVal1">
      <xsl:call-template name="str-split-to-words">
        <xsl:with-param name="pStr" select="string(/*/@att1)"/>
        <xsl:with-param name="pDelimiters" select="';'"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="vrtfVal2">
      <xsl:call-template name="str-split-to-words">
        <xsl:with-param name="pStr" select="/*/@att2"/>
        <xsl:with-param name="pDelimiters" select="';'"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="vVal1"
     select="ext:node-set($vrtfVal1)/word"/>
    <xsl:variable name="vVal2"
     select="ext:node-set($vrtfVal2)/word"/>

     <xsl:for-each select="$vVal1">
       <xsl:variable name="vV1" select="."/>

       <xsl:for-each select="$vVal2">
         <xsl:value-of select="concat($vV1, ., ' ')"/>
       </xsl:for-each>
     </xsl:for-each>
     
  </xsl:template>
</xsl:stylesheet>