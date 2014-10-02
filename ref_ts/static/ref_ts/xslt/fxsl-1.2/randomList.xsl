<!--
===========================================================================
 Stylesheet: random.xsl           List Randomization Functions             
    Version: 1.0 (2002-05-03)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->
<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:myIncrement="f:myIncrement" 
 xmlns:x="f:fxslRandomList.xsl"
 exclude-result-prefixes="xsl ext myIncrement x"
>

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->
  <xsl:import href="random.xsl"/>
  
 
  <!--
      Template: randScale                                     
      Purpose : Return an integer, scaled from [0, modulus-1] 
                to [s, t]                                     
    Parameters:                                               
     $pStart    - [optional] the start of the target interval 
     $pEnd      - [optional] the end of the target interval   
     $pN        - The number N to be scaled                   
  ============================================================-->
  
<!--
  > _randScale :: Float -> Float -> Int -> Int                     
  > randScale s t n = floor (rndScl ((t - s + 1)/dintRange ) s n)  
  >    where    dintRange = fromInt (modulus - 1)                  
                                                                   
                                                                   
  > rndScl :: Float -> Float -> Int -> Float                       
  > rndScl a b n = a * fromInt n + b                               
-->  
  <xsl:template name="_randScale" >
    <xsl:param name="arg2" select="0"/> <!--pStart-->
    <xsl:param name="arg3" select="1"/> <!--pEnd  -->
    <xsl:param name="arg1"/>            <!--pN    -->
    
    <xsl:value-of 
         select="floor( ($arg3 - $arg2 + 1) div ($modulus - 1) 
                         * $arg1 
                        + $arg2 
                       )"/>
  </xsl:template>

<!--
      Template: _dScale                                    
      Purpose : Used to prepare a random recursive index   
                for a list from a random sequence with the 
                same number of elements                    
    Parameters:                                            
     $pRandSeq  - a list of (random) numbers               
        Result: - a random recursive index                 
  =========================================================-->
  <xsl:template name="_dScale">
    <xsl:param name="pRandSeq" select="/.."/>
<!--
                                                            
    > dScale  :: [Int] -> [Int]                             
    > dScale   [] = []                                      
    > dScale (x:xs) = fstScale : (dScale xs)                
    >   where fstScale = randScale 0 (fromInt (length xs)) x
-->
    <xsl:if test="$pRandSeq">
      <el>
        <xsl:call-template name="_randScale">
          <xsl:with-param name="arg2" select="1"/> <!--s-->
          <xsl:with-param name="arg3" 
                      select="count($pRandSeq)"/> <!--end-->
          <xsl:with-param name="arg1" select="$pRandSeq[1]"/>
        </xsl:call-template>
      </el>
      
      <xsl:call-template name="_dScale">
        <xsl:with-param name="pRandSeq" 
                        select="$pRandSeq[position() > 1]"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>
   
<!--
      Template: _randomRecursiveIndex                      
      Purpose : Used to prepare a random recursive index   
                for a list                                 
    Parameters:                                            
     $pList     - a list to be presented in a random order 
     $pSeed     - [optional] a seed for generation of the  
                  random sequence                          
        Result: - a random recursive index                 
  =========================================================-->

<!--
   > randomRecursiveIndex xs  sd 
            = dScale (take (length xs) (randomSequence sd))
-->
  <xsl:template name="_randomRecursiveIndex">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>
    
    <xsl:variable name="vRandSequence">
      <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="count($pList)"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="_dScale">
      <xsl:with-param name="pRandSeq" 
           select="ext:node-set($vRandSequence)/*"/>
    </xsl:call-template>
  </xsl:template>

<!--
      Template: _permutationFromRecursiveIndex             
                                                           
      Purpose : Produce a random permutation of a list     
                based on a given random recursive index    
    Parameters:                                            
     $pList     - a list to be presented in a random order 
     $pIndex    - a list with the same length as $pList    
                  containing the random recursive index    
        Result: - a randomly permuted list                 
  =========================================================-->
  
  <xsl:template name="_permutationFromRecursiveIndex">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pRecIndex" select="/.."/>
    
    <xsl:if test="not(count($pList) = count($pRecIndex))">
      <xsl:message terminate="yes">
       Error[permutationFromRecursiveIndex]: 
             The two lists are not the same length!
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_permRecIdx">
      <xsl:with-param name="pList" select="$pList"/>
      <xsl:with-param name="pRecIndex" select="$pRecIndex"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="_permRecIdx">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pRecIndex" select="/.."/>
    
    <xsl:variable name="vIndex" 
                  select="number($pRecIndex[1])"/>
                  
    <xsl:if test="$pList">
      <el>
        <xsl:value-of 
            select="$pList[position() = $vIndex]"/>
      </el>
    
      <xsl:call-template name="_permRecIdx">
        <xsl:with-param name="pList" 
          select="$pList[position() != $vIndex]"/>
        <xsl:with-param name="pRecIndex" 
             select="$pRecIndex[position() > 1]"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

<!--
      Template: randomizeList                              
                                                           
      Purpose : Produce a random permutation of a list     
                based on a given seed for randomisation    
    Parameters:                                            
     $pList     - a list to be reproduced in a random order
     $pSeed     - [optional] the seed to be used           
  =========================================================-->
  
  <xsl:template name="randomizeList">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>
    
    <xsl:variable name="vrtfRecIndex">
      <xsl:call-template name="_randomRecursiveIndex">
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vRecIndex" 
              select="ext:node-set($vrtfRecIndex)/*"/>
              
    <xsl:call-template name="_permutationFromRecursiveIndex">
      <xsl:with-param name="pList" select="$pList"/>
      <xsl:with-param name="pRecIndex" select="$vRecIndex"/>
    </xsl:call-template>
  </xsl:template>

<!--
      Template: _mapFromRandIndex                          
                                                           
      Purpose : Produce a mapping of a given function      
                over a list, which will be applied randomly
                based on a given random recursive index    
    Parameters:                                            
     $pFun      - a template reference to a function       
     $pList     - a list to be processed in a random order 
     $pIndex    - a list with the same length as $pList    
                  containing the random recursive index    
        Result: - a mapping of pFun applied in random order
                  (specified by pIndex) on pList           
  =========================================================-->
  
  <xsl:template name="_mapFromRandIndex">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pRecIndex" select="/.."/>
    
    <xsl:if test="not(count($pList) = count($pRecIndex))">
      <xsl:message terminate="yes">
       Error[mapFromRandIndex]: 
             The two lists are not the same length!
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_mapRndIndex">
      <xsl:with-param name="pFun" select="$pFun"/>
      <xsl:with-param name="pList" select="$pList"/>
      <xsl:with-param name="pRecIndex" select="$pRecIndex"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="_mapRndIndex">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pRecIndex" select="/.."/>
    
    <xsl:variable name="vIndex" 
                  select="number($pRecIndex[1])"/>
                  
    <xsl:if test="$pList">
      <el>
        <xsl:apply-templates select="$pFun">
          <xsl:with-param name="arg1" 
           select="$pList[position() = $vIndex]"/>
        </xsl:apply-templates>
      </el>
    
      <xsl:call-template name="_mapRndIndex">
        <xsl:with-param name="pFun" select="$pFun"/>
        <xsl:with-param name="pList" 
          select="$pList[position() != $vIndex]"/>
        <xsl:with-param name="pRecIndex" 
             select="$pRecIndex[position() > 1]"/>
      </xsl:call-template>
    </xsl:if>
  </xsl:template>

<!--
      Template: randomMap                                  
                                                           
      Purpose : Produce a mapping of a given function      
                over a list, which will be applied randomly
                based on a given seed for randomization    
    Parameters:                                            
     $pFun      - a template reference to a function       
     $pList     - a list to be processed in a random order 
     $pSeed     - [optional] the seed to be used           
                   for randomization                       
  =========================================================-->
  
  <xsl:template name="randomMap">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>
    
    <xsl:variable name="vrtfRecIndex">
      <xsl:call-template name="_randomRecursiveIndex">
        <xsl:with-param name="pList" select="$pList"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vRecIndex" 
              select="ext:node-set($vrtfRecIndex)/*"/>
              
    <xsl:call-template name="_mapFromRandIndex">
      <xsl:with-param name="pFun" select="$pFun"/>
      <xsl:with-param name="pList" select="$pList"/>
      <xsl:with-param name="pRecIndex" select="$vRecIndex"/>
    </xsl:call-template>
  </xsl:template>
 
<!--
      Template: randListIndex                              
                                                           
      Purpose : Produce a random (non-recursive)           
                index for a list                           
    Parameters:                                            
     $pList     - the list for which to                    
                  produce a random index                   
     $pSeed     - [optional] the seed to be used           
                   for randomization                       
  =========================================================-->
  
  <xsl:template name="randListIndex">
    <xsl:param name="pList" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>

    <xsl:variable name="vFunIncr" 
                  select="$x:st/myIncrement:*[1]"/>
    <xsl:variable name="vrtfNums">
      <xsl:call-template name="scanIter">
        <xsl:with-param name="arg1" select="count($pList) - 1"/>
        <xsl:with-param name="arg2" select="$vFunIncr"/>
        <xsl:with-param name="arg3" select="'1'"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="randomizeList">
      <xsl:with-param name="pList" 
                      select="ext:node-set($vrtfNums)/*"/>
      <xsl:with-param name="pSeed" select="$pSeed"/>
    </xsl:call-template>

  </xsl:template>
  
  <xsl:template match="myIncrement:*">
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="$arg1 + 1"/>
  </xsl:template>
  

  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
   <xsl:variable name="x:st" select="document('')/*"/>

<!--
      a template reference to an incrementing function                       
  ========================================================================== -->
   <myIncrement:myIncrement/>

</xsl:stylesheet>