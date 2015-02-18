<!--
===========================================================================
 Stylesheet: combinatorics.xsl    COMBINATORIAL ALGORITHMS                 
    Version: 1.0 (2002-03-24)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->

<xsl:stylesheet version="1.0"
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:injectValues="f:comb-injectValues"
 xmlns:extendAllLists="f:comb-extendAllLists"
 xmlns:appendToList="f:comb-appendToList"
 xmlns:x="f:combinatorics.xsl"
 exclude-result-prefixes="xsl x ext injectValues extendAllLists
 appendToList"
 >

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->

  <xsl:import href="foldl.xsl"/>
  <xsl:import href="map.xsl"/>
  <xsl:import href="curry.xsl"/>
  <xsl:import href="concat.xsl"/>

<!--
  ==========================================================================
    Module Interface:                                                       
  ==========================================================================
-->
   
<!--
    Template: cartProduct                                                    
     Purpose: Return the cartesian product of the elements from N givenlists 
  Parameters:                                                                
    $pLists - a nodeset, each element of which has a list of children        
              The cartesian product of the elements of all such lists        
              will be produced                                               
 =========================================================================== 
-->
  <xsl:template name="cartProduct">
<!--
    This is the implemented algorithm:                                       
                                                                             
    > cartProduct yss = foldl injectValues [ [] ] yss                        
    >  where                                                                 
    >   injectValues xss ys = concat ( (map (extendAllLists xss)) ys)        
    >   extendAllLists xss y = map (++ [y]) xss                              
                                                                             
-->

    <xsl:param name="pLists" select="/.."/>
    
    <xsl:variable name="vrtf-cp">
      <xsl:element name="result"/>
    </xsl:variable>
    
    <xsl:variable name="vInjectValues" select="$x:vst/injectValues:*[1]"/>
    
    <xsl:call-template name="foldl">
      <xsl:with-param name="pFunc" select="$vInjectValues"/>
      <xsl:with-param name="pA0" select="ext:node-set($vrtf-cp)/*"/>
      <xsl:with-param name="pList" select="$pLists"/>
    </xsl:call-template>
    
  </xsl:template>


  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
  <xsl:variable name="x:vst" select="document('')/*"/>
  <!-- internal use only - for applying the functions:               
      extendAllLists                                                     
      injectValues                                                      
-->
   <injectValues:injectValues/>
   <extendAllLists:extendAllLists/>
   <appendToList:appendToList/>
  <!-- internally used templates -->
  
<!--  >   injectValues xss ys = concat ( (map (extendAllLists xss)) ys) -->

  <xsl:template name="injectValues" match="injectValues:*">
    <xsl:param name="arg1" select="/.."/> <!-- List of lists (Result)-->
    <xsl:param name="arg2" select="/.."/> <!-- Current list -->
    
    <xsl:variable name="vextAllLists" select="$x:vst/extendAllLists:*[1]"/>
    
    <xsl:variable name="vrtf-curriedExtendAllLists">
      <xsl:call-template name="curry">
        <xsl:with-param name="pFun" select="$vextAllLists"/>
        <xsl:with-param name="pNargs" select="2"/>
        <xsl:with-param name="arg2" select="$arg1"/>
        <xsl:with-param name="pStripAuxNamespace" select="1"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vthisExtendAllLists" 
     select="ext:node-set($vrtf-curriedExtendAllLists)/*"/>
     
     <xsl:variable name="vrtf-MoreDeeper">
       <xsl:call-template name="map">
         <xsl:with-param name="pFun" select="$vthisExtendAllLists"/>
         <xsl:with-param name="pList1" select="$arg2/*"/>
       </xsl:call-template>
     </xsl:variable>
     
     <xsl:call-template name="concat">
       <xsl:with-param name="arg1" 
            select="ext:node-set($vrtf-MoreDeeper)/*"/>
     </xsl:call-template>
  </xsl:template>
  
<!--   >   extendAllLists xss y = map (++ [y]) xss -->  
                           
   <xsl:template name="extLists" match="extendAllLists:*">
    <xsl:param name="arg2" select="/.."/> <!-- List of lists -->
    <xsl:param name="arg1" select="/.."/> <!-- Extending element -->
    
    <xsl:variable name="vappendToList" select="$x:vst/appendToList:*[1]"/>

    <xsl:variable name="vrtf-vappendElement">
      <xsl:call-template name="curry">
        <xsl:with-param name="pFun" select="$vappendToList"/>
        <xsl:with-param name="pNargs" select="2"/>
        <xsl:with-param name="arg2" select="$arg1"/>
        <xsl:with-param name="pStripAuxNamespace" select="1"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vappendElement" 
     select="ext:node-set($vrtf-vappendElement)/*"/>
    
    <xsl:call-template name="map">
      <xsl:with-param name="pFun" select="$vappendElement"/>
      <xsl:with-param name="pList1" select="$arg2"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template match="appendToList:*">
    <xsl:param name="arg1" select="/.."/> <!-- List -->
    <xsl:param name="arg2" select="/.."/> <!-- new element -->
    
      <xsl:copy-of select="$arg1/*"/>
      <xsl:copy-of select="$arg2"/>
  </xsl:template>
  
</xsl:stylesheet>