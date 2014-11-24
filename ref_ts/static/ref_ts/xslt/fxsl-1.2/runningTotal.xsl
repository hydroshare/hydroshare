<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:myAdd ="f:myAdd"
xmlns:myMult="f:myMult"
>
  <xsl:import href="zipWith.xsl"/>
  <xsl:import href="scanl.xsl"/>
  
  <!-- To be applied on: booklist.xml -->

  <myAdd:myAdd/>
  <myMult:myMult/>

  <xsl:output omit-xml-declaration="yes"/>
  <xsl:template match="/">
    <html>
      <table border="2">
       <tr><th>Title</th><th>Author</th><th>Price</th>
           <th>Sales</th><th>Current Total</th>
       </tr>
       <xsl:call-template name="myRunningTotal">
         <xsl:with-param name="vNodes"
                         select="/booklist/book"/>
       </xsl:call-template>
      </table>
    </html>
  </xsl:template>
  
  <xsl:template name="myRunningTotal">
    <xsl:param name="vNodes" select="/.."/>
    
    <xsl:variable name="vFunAdd" select="document('')/*/myAdd:*[1]"/>
    <xsl:variable name="vFunMult" select="document('')/*/myMult:*[1]"/>

    <xsl:variable name="vrtfSingleBookAmounts">
      <xsl:call-template name="zipWith">
        <xsl:with-param name="pFun" select="$vFunMult"/>
        <xsl:with-param name="pList1" select="$vNodes/price"/>
        <xsl:with-param name="pList2" select="$vNodes/sales"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vrtfRunningTotal">
      <xsl:call-template name="scanl1">
        <xsl:with-param name="pFun" select="$vFunAdd"/>
        <xsl:with-param name="pList"
                select="ext:node-set($vrtfSingleBookAmounts)/*"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vRunningTotal"
    select="ext:node-set($vrtfRunningTotal)/*"/>
    
    <xsl:for-each select="$vNodes">
        <xsl:variable name="vThisPosition" select="position()"/>
        <tr>
           <td><xsl:value-of select="title"/></td>
           <td><xsl:value-of select="price"/></td>
           <td><xsl:value-of select="sales"/></td>
           <td><xsl:value-of select="sales * price"/></td>
           <td><xsl:value-of select="$vRunningTotal
                                         [$vThisPosition]"/>
           </td>
        </tr>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template match="myAdd:*">
    <xsl:param name="pArg1"/>
    <xsl:param name="pArg2"/>

    <xsl:value-of select="$pArg1 + $pArg2"/>
  </xsl:template>

  <xsl:template match="myMult:*">
    <xsl:param name="pArg1"/>
    <xsl:param name="pArg2"/>

    <xsl:value-of select="$pArg1 * $pArg2"/>
  </xsl:template>
</xsl:stylesheet>