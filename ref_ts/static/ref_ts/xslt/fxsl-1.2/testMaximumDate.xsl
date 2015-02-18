<xsl:stylesheet version="1.0"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
xmlns:MycompareDates="MycompareDates"
exclude-result-prefixes="xsl MycompareDates"
>
   <xsl:import href="maximum.xsl"/>
   
   <xsl:output omit-xml-declaration="yes"/>
   
   <!-- This transformation must be applied to:
        date-time.xml 
    -->
   
     <MycompareDates:MycompareDates/>

    <xsl:template match="/">
      <xsl:variable name="vCMPFun" select="document('')/*/MycompareDates:*[1]"/>

      <xsl:variable name="vrtfResult">
        <xsl:call-template name="maximum">
          <xsl:with-param name="pList" select="/*/*"/>
          <xsl:with-param name="pCMPFun" select="$vCMPFun"/> 
        </xsl:call-template>
      </xsl:variable>
      
      <xsl:value-of select="ext:node-set($vrtfResult)/*/subject"/>
    </xsl:template>

    <xsl:template name="MycompareDates" match="MycompareDates:*">
         <xsl:param name="arg1"/>
         <xsl:param name="arg2"/>
         
         <xsl:variable name="vDate1" 
              select="translate($arg1/date, '/', '')"/>
         
         <xsl:variable name="vDate2" 
              select="translate($arg2/date, '/', '')"/>
         
         <xsl:choose>
          <xsl:when test="$vDate1 > $vDate2">1</xsl:when>
          <xsl:when test="$vDate1 = $vDate2">
            <xsl:variable name="vTime1" 
             select="translate($arg1/time, ':APM', '')
                    +
                     120000 * (substring($arg1/time, 9,2)='PM')"/>

            <xsl:variable name="vTime2" 
             select="translate($arg1/time, ':APM', '')
                    +
                     120000 * (substring($arg1/time, 9,2)='PM')"/>
            <xsl:if test="$vTime1 > $vTime2">1</xsl:if>
          </xsl:when>
         </xsl:choose>
    </xsl:template>
</xsl:stylesheet>