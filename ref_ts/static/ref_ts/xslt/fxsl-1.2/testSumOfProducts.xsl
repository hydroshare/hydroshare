<xsl:stylesheet version="1.0" 
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:test-map-product="test-map-product"
exclude-result-prefixes="xsl ext test-map-product"
>
   <xsl:import href="sum.xsl"/>
   <xsl:import href="map.xsl"/>
   <xsl:import href="product.xsl"/>

   <!-- This transformation is to be applied on:
        salesMap.xml
        
        It contains the code of the "sum of products" from the 
        article "The Functional Programming Language XSLT"
     -->

   <test-map-product:test-map-product/>
   
   <xsl:output method="text"/>
 
   <xsl:template match="/">
     <!-- Get: map product /sales/sale -->
     <xsl:variable name="vSalesTotals">
         <xsl:variable name="vTestMap" select="document('')/*/test-map-product:*[1]"/>
         <xsl:call-template name="map">
           <xsl:with-param name="pFun" select="$vTestMap"/>
           <xsl:with-param name="pList1" select="/sales/sale"/>
         </xsl:call-template>
     </xsl:variable>

     <!-- Get sum map product /sales/sale -->
      <xsl:call-template name="sum">
        <xsl:with-param name="pList" select="ext:node-set($vSalesTotals)/*"/>
      </xsl:call-template>
   </xsl:template>

    <xsl:template name="makeproduct" match="*[namespace-uri() = 'test-map-product']">
      <xsl:param name="arg1"/>

      <xsl:call-template name="product">
        <xsl:with-param name="pList" select="$arg1/*"/>
      </xsl:call-template>
    </xsl:template>
</xsl:stylesheet>