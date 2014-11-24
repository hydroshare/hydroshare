<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:map-foldl-func="map-foldl-func"
exclude-result-prefixes="xsl ext map-foldl-func"
>
   <xsl:import href="dvc-str-foldl.xsl"/>

   <map-foldl-func:map-foldl-func/>
   
     <xsl:template name="str-dvc-map">
      <xsl:param name="pFun" select="/.."/>
      <xsl:param name="pStr" select="/.."/>

       <xsl:variable name="vFoldlFun" select="document('')/*/map-foldl-func:*[1]"/>
       
	   <xsl:variable name="vFuncComposition">
	     <xsl:copy-of select="$vFoldlFun"/>
	     <xsl:copy-of select="$pFun"/>
	   </xsl:variable>
	   
	   <xsl:variable name="vFComposition" 
	                 select="ext:node-set($vFuncComposition)/*"/>

      <xsl:call-template name="dvc-str-foldl">
        <xsl:with-param name="pFunc" select="$vFComposition"/>
        <xsl:with-param name="pStr" select="$pStr"/>
        <xsl:with-param name="pA0" select="/.."/>
      </xsl:call-template>
    </xsl:template>


    <xsl:template name="mapL" match="*[namespace-uri() = 'map-foldl-func']">
         <xsl:param name="arg0" select="/.."/>
         <xsl:param name="arg1" select="/.."/>
         <xsl:param name="arg2" select="/.."/>
         
         <!-- $arg1 must be A0 -->
         <xsl:copy-of select="$arg1"/>
         
           <xsl:apply-templates select="$arg0[1]">
             <xsl:with-param name="arg1" select="substring($arg2,1,1)"/>
           </xsl:apply-templates>
    </xsl:template>
    

</xsl:stylesheet>