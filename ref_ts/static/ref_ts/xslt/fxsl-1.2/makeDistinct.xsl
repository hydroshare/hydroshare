<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:mytestElem="f:mytestElem"
>
    <xsl:import href="foldl.xsl"/>
    
    <xsl:output indent="yes" omit-xml-declaration="yes"/>
    <mytestElem:mytestElem/>
    <xsl:template match="/">
      <xsl:variable name="vFun-testElem"
                    select="document('')/*/mytestElem:*[1]"/>

      <xsl:call-template name="foldl">
        <xsl:with-param name="pFunc" select="$vFun-testElem"/>
        <xsl:with-param name="pA0" select="/.."/>
        <xsl:with-param name="pList"
                        select="document('testDistinct11.xml')/itemList/item
                              | document('testDistinct22.xml')/itemList/item
                              | document('testDistinct33.xml')/itemList/item"
      />
      </xsl:call-template>
    </xsl:template>
    
    <xsl:template match="mytestElem:*">
      <xsl:param name="arg1" select="/.."/>
      <xsl:param name="arg2" select="/.."/>
      
      <xsl:copy-of select="$arg1"/>
      <xsl:if test="not($arg2/@name = $arg1/@name)">
        <xsl:copy-of select="$arg2"/>
      </xsl:if>
    </xsl:template>
</xsl:stylesheet>