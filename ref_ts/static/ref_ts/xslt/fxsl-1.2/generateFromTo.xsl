<xsl:stylesheet version="1.0" 
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:ext="http://exslt.org/common"
  xmlns:myIncrement="f:myIncrement" 
  exclude-result-prefixes="ext myIncrement" 
 >
 
 <xsl:import href="iter.xsl"/>
 <!-- To be applied on any xml file -->
 
 <xsl:output omit-xml-declaration="yes" indent="yes"/>
 
  <xsl:template match="/">
    <xsl:call-template name="generateBatch">
      <xsl:with-param name="pFrom" select="3"/>
      <xsl:with-param name="pTo" select="7"/>
    </xsl:call-template>
  </xsl:template>
  
  <myIncrement:myIncrement/>
  
  <xsl:template name="generateBatch">
    <xsl:param name="pFrom"/>
    <xsl:param name="pTo"/>
    
    <xsl:variable name="vFunIncr" 
         select="document('')/*/myIncrement:*[1]"/>
    
    <xsl:variable name="vResult">
      <xsl:call-template name="scanIter">
        <xsl:with-param name="arg1" select="$pTo - $pFrom + 1"/>
        <xsl:with-param name="arg2" select="$vFunIncr"/>
        <xsl:with-param name="arg3" select="$pFrom - 1"/>
        <xsl:with-param name="arg4" select="'obj'"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:copy-of select="ext:node-set($vResult)/*[position() > 1]"/>
   </xsl:template>
   
   <xsl:template match="myIncrement:*">
     <xsl:param name="arg1"/>
       <childnode>
       <xsl:value-of select="$arg1 + 1"/>
       </childnode>
   </xsl:template>

</xsl:stylesheet>