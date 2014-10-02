<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:ext="http://exslt.org/common"
>

  <xsl:import href="store.xsl"/>
  
  <!-- to be applied on any xml source -->
  
  <xsl:output method="text"/>  

  <xsl:template match="/"> 
    <!-- Get Initial Store -->
    <xsl:variable name="vrtfStore0">
      <xsl:call-template name="getInitialStore"/>
    </xsl:variable>
    
    <xsl:variable name="vStore0" select="ext:node-set($vrtfStore0)/*"/>
    
    <!-- Get A, B, C from the initial store: must be 0-s -->
      vStore0:
      A='<xsl:apply-templates select="$vStore0/*[local-name() = 'getValue']">
          <xsl:with-param name="pName" select="'A'"/>
         </xsl:apply-templates>'
      B='<xsl:apply-templates select="$vStore0/*[local-name() = 'getValue']">
          <xsl:with-param name="pName" select="'B'"/>
         </xsl:apply-templates>'
      C='<xsl:apply-templates select="$vStore0/*[local-name() = 'getValue']">
          <xsl:with-param name="pName" select="'C'"/>
         </xsl:apply-templates>'

    <!-- Update store0 with 'A=1' -->
    <xsl:variable name="vrtfStore1">
      <xsl:apply-templates select="$vStore0/*[local-name() = 'updateStore']">
        <xsl:with-param name="pName" select="'A'"/>
        <xsl:with-param name="pValue" select="1"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:variable name="vStore1" select="ext:node-set($vrtfStore1)/*"/>
    <!-- Get A, B, C from the store1: A is 1, the rest must be 0-s -->
      vStore1:
      A='<xsl:apply-templates select="$vStore1/*[local-name() = 'getValue']">
          <xsl:with-param name="pName" select="'A'"/>
         </xsl:apply-templates>'
      B='<xsl:apply-templates select="$vStore1/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'B'"/>
         </xsl:apply-templates>'
      C='<xsl:apply-templates select="$vStore1/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'C'"/>
         </xsl:apply-templates>'
    
    <!-- Update store1 with 'B=2' -->
    <xsl:variable name="vrtfStore2">
      <xsl:apply-templates select="$vStore1/*[local-name() = 'updateStore']">
        <xsl:with-param name="pName" select="'B'"/>
        <xsl:with-param name="pValue" select="2"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:variable name="vStore2" select="ext:node-set($vrtfStore2)/*"/>
    <!-- Get A, B, C from the store2: A is 1, B is 2, the rest must be 0-s -->
      vStore2:
      A='<xsl:apply-templates select="$vStore2/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'A'"/>
         </xsl:apply-templates>'
      B='<xsl:apply-templates select="$vStore2/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'B'"/>
         </xsl:apply-templates>'
      C='<xsl:apply-templates select="$vStore2/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'C'"/>
         </xsl:apply-templates>'
    
    <!-- Update store2 with 'C=3' -->
    <xsl:variable name="vrtfStore3">
      <xsl:apply-templates select="$vStore2/*[local-name() = 'updateStore']">
        <xsl:with-param name="pName" select="'C'"/>
        <xsl:with-param name="pValue" select="3"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:variable name="vStore3" select="ext:node-set($vrtfStore3)/*"/>
    <!-- Get A, B, C from the store3: A is 1, B is 2, C is 3, the rest must be 0-s -->
      vStore3:
      A='<xsl:apply-templates select="$vStore3/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'A'"/>
         </xsl:apply-templates>'
      B='<xsl:apply-templates select="$vStore3/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'B'"/>
         </xsl:apply-templates>'
      C='<xsl:apply-templates select="$vStore3/*[local-name() = 'getValue']">
           <xsl:with-param name="pName" select="'C'"/>
         </xsl:apply-templates>'
   </xsl:template>
</xsl:stylesheet>