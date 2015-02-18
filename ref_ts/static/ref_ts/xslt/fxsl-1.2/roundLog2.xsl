<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:lxslt="http://xml.apache.org/xslt"
xmlns:roundLog2="roundLog2"
extension-element-prefixes="roundLog2"
>
  <xsl:template name="roundLog2">
    <xsl:param name="pX"/>
    <xsl:value-of select="roundLog2:roundLog2(string($pX))"/>
  </xsl:template>
  
 
  <lxslt:component prefix="roundLog2" functions="roundLog2">
    <lxslt:script lang="javascript">
       function roundLog2(x)
       {
          return Math.round(Math.log(x)/Math.LN2);
       }
    </lxslt:script>
  </lxslt:component>
</xsl:stylesheet>

