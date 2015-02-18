<!--
===========================================================================
 Stylesheet: random.xsl           Randomization Functions                  
    Version: 1.0 (2002-03-16)                                              
   Based on: Random number algorithms in Simon Thompson's                  
             "Haskell, the craft of functional programming"                
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->
<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:randScale="f:randScale"
 xmlns:myRandNext="f:myRandNext" 
 xmlns:mySingleRandDistFun="f:mySingleRandDistFun" 
 xmlns:x="f:fxslRandom.xsl"
 exclude-result-prefixes="xsl ext randScale myRandNext mySingleRandDistFun x"
>

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->
  <xsl:import href="map.xsl"/>
  <xsl:import href="curry.xsl"/>
  <xsl:import href="iter.xsl"/>
  
<!--
  ==========================================================================
    Global Randomizing constants:                                           
  ==========================================================================-->
  <xsl:variable name="seed"       select="17489"/>
  <xsl:variable name="multiplier" select="25173"/>
  <xsl:variable name="increment"  select="13849"/>
  <xsl:variable name="modulus"    select="65536"/>
  
<!--
	This is a linear congruental method of generating                          
	a pseudo-random sequence of natural numbers                                
	starting with a seed and then getting the next element                     
	of the sequence from the previous value like this:                         
	                                                                           
	nextRand :: Int -> Int                                                     
	nextRand n = (multiplier * n + increment) `mod` modulus                    
-->  
  
<!--
      Template: randNext                                                     
      Purpose : Return the value of the next random number from the current  
    Parameters:                                                              
         $arg1  - the current random number, from which to produce the next  
  ========================================================================== -->
  <xsl:template name="randNext" match="myRandNext:*">
    <xsl:param name="arg1"/>
    
    <xsl:value-of select="($multiplier * $arg1 + $increment) mod $modulus"/>
  </xsl:template>

<!--
      Template: scaleSequence                                                
      Purpose : Return a scaled version of a sequence from a given sequence  
    Parameters:                                                              
       $pStart  - [optional] the start of the interval, in which randoms     
                   are to be produced                                        
       $pEnd    - [optional] the end of the interval, in which randoms       
                   are to be produced                                        
       $pList   - the list of numbers that are to be scaled                  
  ========================================================================== -->
  <xsl:template name="scaleSequence">
    <xsl:param name="pStart" select="0"/>
    <xsl:param name="pEnd" select="1"/>
    <xsl:param name="pList" select="/.."/>
    
    <xsl:variable name="vScaleFun" select="$x:st/randScale:*[1]"/>
    <xsl:variable name="vRange" select="$pEnd - $pStart + 1"/>
    
    <xsl:variable name="vrtfCurriedScale">
      <xsl:call-template name="curry">
        <xsl:with-param name="pFun" select="$vScaleFun"/>
        <xsl:with-param name="pNargs" select="3"/>
        <xsl:with-param name="arg2" select="$pStart"/>
        <xsl:with-param name="arg3" select="$vRange"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vFixedScaleFun" 
                  select="ext:node-set($vrtfCurriedScale)/*"/>
                  
    <xsl:call-template name="map">
      <xsl:with-param name="pFun" select="$vFixedScaleFun"/>
      <xsl:with-param name="pList1" select="$pList"/>
    </xsl:call-template>
  </xsl:template>
  
  
<!--
      Template: randomSequence                                              
      Purpose : Return a sequence of random numbers starting from a seed    
    Parameters:                                                             
      $pLength  - [optional] the length of the sequence of randoms          
                  that must be produced                                     
      $pSeed    - [optional] the seed for the randomization                 
      $pStart   - [optional] the start of the interval,                     
                  in which randoms are to be produced                       
      $pEnd     - [optional] the end of the interval,                       
                  in which randoms are to be produced                       
  ==========================================================================-->
  <xsl:template name="randomSequence">
    <xsl:param name="pLength" select="1"/>
    <xsl:param name="pSeed" select="$seed"/>
    <xsl:param name="pStart" select="0"/>
    <xsl:param name="pEnd" select="$modulus - 1"/>
    
    <xsl:variable name="vFunRandNext" select="$x:st/myRandNext:*[1]"/>
    
    <xsl:variable name="vrtfUnscaledSeq">
	    <xsl:call-template name="scanIter">
	      <xsl:with-param name="arg1" select="$pLength - 1"/><!-- n -->
	      <xsl:with-param name="arg2" select="$vFunRandNext"/><!-- f -->
	      <xsl:with-param name="arg3" select="$pSeed"/> <!-- x -->
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="$pStart = 0 and $pEnd = $modulus - 1">
        <xsl:copy-of select="ext:node-set($vrtfUnscaledSeq)/*"/>
      </xsl:when>
      <xsl:otherwise>
		    <xsl:call-template name="scaleSequence">
			    <xsl:with-param name="pStart" select="$pStart"/>
			    <xsl:with-param name="pEnd" select="$pEnd"/>
			    <xsl:with-param name="pList" select="ext:node-set($vrtfUnscaledSeq)/*"/>
		    </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
<!--
Sometimes we want that each outcome must have a predefined probability.            
First we define a "Distribution" type, which is a list of pairs of "outcome object"
and "oucome object's probability":                                                 
                                                                                   
In order for this to make sense, the objects in the list must all be distinct,     
and their probabilities must sum up to 1.                                          
                                                                                   
> type Distribution a  = [(a, Float)]                                              
                                                                                   
                                                                                   
Suppose we need to model random outcomes 1 to 6 each with its given probability:   
                                                                                   
                                                                                   
> dist1 :: Distribution Int                                                        
> dist1 = [(1, 0.2), (2, 0.25), (3, 0.25), (4, 0.15), (5, 0.1), (6, 0.05)]         
                                                                                   
                                                                                   
We will use a function, which given a distribution produces another function,      
that maps the interval (0 to 65535) into the set of distinct objects according     
to their probability. The idea is to divide the interval 0-65535 into N intervals  
(where N = length(dist) is the number of distinct objects), but in such a way,     
that the lengths of these intervals are proportional to the probabilities of the   
corresponding objects.                                                             
                                                                                   
                                                                                   
> makeFunction :: Distribution a -> (Float -> a)                                   
> makeFunction dist = makeFun dist 0.0                                             
                                                                                   
                                                                                   
> makeFun ((ob, p) : dist) nLast rand                                              
>                                                                                  
>   | nNext >= rand && rand > nLast                                                
>         =  ob                                                                    
>                                                                                  
>   | otherwise                                                                    
>         = makeFun dist nNext rand                                                
>           where                                                                  
>                nNext = p*fromInt modulus + nLast                                 
                                                                                   
                                                                                   
Then the transformation of a list of random numbers into a list of                 
(weighted) random numbers according to a distribution dist is given                
by the expression:                                                                 
                                                                                   
map (makeFunction dist)                                                            
-->

<!--
      Template: dist-randomSequence                                          
      Purpose : Return the value of the next random number from the current  
    Parameters:                                                              
      $pLength  - [optional] the length of the sequence of randoms           
                   that must be produced                                     
      $pDist    - a list of distributions (outcome,probability pairs)        
                  e.g.:                                                      
                    <myDistribution:myDistribution>                          
                      <o>1</o><p>0.2</p>                                     
                      <o>2</o><p>0.25</p>                                    
                      <o>3</o><p>0.25</p>                                    
                      <o>4</o><p>0.15</p>                                    
                      <o>5</o><p>0.1</p>                                     
                      <o>6</o><p>0.05</p>                                    
                    </myDistribution:myDistribution>                         
                                                                             
    $pSeed      - [optional] the seed for the randomization                  
  ========================================================================== -->
  <xsl:template name="dist-randomSequence">
    <xsl:param name="pLength" select="1"/>
    <xsl:param name="pDist" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>
    
    <xsl:variable name="vrtfNormalRandomSeq">
      <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="$pLength"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>

    <xsl:variable name="vmakeFun" 
                  select="$x:st/mySingleRandDistFun:*[1]"/>
    
    <!-- build makeFun dist 0.0 -->
    <xsl:variable name="vrtfDistFunction">
      <xsl:call-template name="curry">
        <xsl:with-param name="pFun" select="$vmakeFun"/>
        <xsl:with-param name="pNargs" select="3"/>
        <xsl:with-param name="arg2" select="$pDist"/>
        <xsl:with-param name="arg3" select="'0.0'"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="map">
      <xsl:with-param name="pFun" select="ext:node-set($vrtfDistFunction)/*"/>
      <xsl:with-param name="pList1" 
                      select="ext:node-set($vrtfNormalRandomSeq)/*"/>
    </xsl:call-template>
  </xsl:template>
  
<!--
      Template: randomSubSequence                                            
      Purpose : Return a sub-sequence of random numbers                      
                starting from a given index                                  
    Parameters:                                                              
     $pLength   - [optional] the length of the sequence of randoms           
                   that must be produced                                     
     $pSubStart - [optional] the index at which the sub-sequence is to start 
     $pSeed     - [optional] the seed for the randomization                  
     $pStart    - [optional] the start of the interval,                      
                  in which randoms are to be produced                        
     $pEnd      - [optional] the end of the interval,                        
                  in which randoms are to be produced                        
  ========================================================================== -->
  <xsl:template name="randomSubSequence">
    <xsl:param name="pLength" select="1"/>
    <xsl:param name="pSubStart" select="1"/>
    <xsl:param name="pSeed" select="$seed"/>
    <xsl:param name="pStart" select="0"/>
    <xsl:param name="pEnd" select="$modulus - 1"/>
    
    <xsl:variable name="vrtfInitSequence">
      <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="$pSubStart"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="$pLength"/>
        <xsl:with-param name="pSeed" 
                        select="ext:node-set($vrtfInitSequence)/*[last()]"/>
        <xsl:with-param name="pStart" select="$pStart"/>
        <xsl:with-param name="pEnd" select="$pEnd"/>
    </xsl:call-template>
  </xsl:template>
  
<!--
      Template: dist-randomSubSequence                                       
      Purpose : Return a sub-sequence of random numbers                      
                starting from a given index, and according to                
                a given distribution                                         
    Parameters:                                                              
     $pLength   - [optional] the length of the sequence of randoms           
                   that must be produced                                     
     $pSubStart - The index at which the sub-sequence is to start            
     $pDist     - a list of distributions (outcome,probability pairs)        
                  e.g.:                                                      
                    <myDistribution:myDistribution>                          
                      <o>1</o><p>0.2</p>                                     
                      <o>2</o><p>0.25</p>                                    
                      <o>3</o><p>0.25</p>                                    
                      <o>4</o><p>0.15</p>                                    
                      <o>5</o><p>0.1</p>                                     
                      <o>6</o><p>0.05</p>                                    
                    </myDistribution:myDistribution>                         
                                                                             
     $pSeed     - [optional] the seed for the randomization                  
  ========================================================================== -->
  <xsl:template name="dist-randomSubSequence">
    <xsl:param name="pLength" select="1"/>
    <xsl:param name="pSubStart" select="1"/>
    <xsl:param name="pDist" select="/.."/>
    <xsl:param name="pSeed" select="$seed"/>

    <xsl:variable name="vrtfInitSequence">
      <xsl:call-template name="randomSequence">
        <xsl:with-param name="pLength" select="$pSubStart"/>
        <xsl:with-param name="pSeed" select="$pSeed"/>
      </xsl:call-template>
    </xsl:variable>
 
    <xsl:call-template name="dist-randomSequence">
        <xsl:with-param name="pLength" select="$pLength"/>
        <xsl:with-param name="pSeed" 
                        select="ext:node-set($vrtfInitSequence)/*[last()]"/>
        <xsl:with-param name="pDist" select="$pDist"/>
    </xsl:call-template>
  </xsl:template>
  
  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
   <xsl:variable name="x:st" select="document('')/*"/>

<!--
      a template reference to a scaling function                             
  ========================================================================== -->
   <randScale:randScale/>
<!--
      a template reference to a distribution-randomizing function            
  ========================================================================== -->
   <mySingleRandDistFun:mySingleRandDistFun/>
  
<!--
      a template reference to randNext                                       
  ========================================================================== -->
  <myRandNext:myRandNext/>
  
  <xsl:template name="makeFun" match="mySingleRandDistFun:*">
    <xsl:param name="arg1"/>              <!-- rand -->
    <xsl:param name="arg2" select="/.."/> <!-- Distribution -->
    <xsl:param name="arg3"/>              <!-- nLast -->
    
    <xsl:variable name="vP" select="$arg2[2]"/>
    <xsl:variable name="vOutcome" select="$arg2[1]"/>
    <xsl:variable name="vnNext" select="$vP * $modulus + $arg3"/>

    <xsl:choose>
			<!--                                     
				>   | nNext >= rand && rand > nLast    
				>         =  ob                        
			-->
      <xsl:when test="$vnNext >= $arg1 and $arg1 > $arg3">
        <xsl:copy-of select="$vOutcome/node()"/>
      </xsl:when>
			<!--
				>   | otherwise                             
				>         = makeFun dist nNext rand         
			-->
      <xsl:otherwise>
        <xsl:call-template name="makeFun">
          <xsl:with-param name="arg1" select="$arg1"/>
          <xsl:with-param name="arg2" select="$arg2[position() > 2]"/>
          <xsl:with-param name="arg3" select="$vnNext"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>    
  </xsl:template>
  
  
<!--   The following  scales a single number n 
       from the interval [0, modulus - 1]      
       to the interval [s, t]                  
                                               
       scale n = n `div` denom + s             
       range   = t - s + 1                     
       denom   = modulus `div` range           

-->  
  <xsl:template match="randScale:*">
    <xsl:param name="arg1"/> <!-- n -->
    <xsl:param name="arg2"/> <!-- s -->
    <xsl:param name="arg3"/> <!-- range -->
    
    <xsl:variable name="vDenom" select="floor($modulus div $arg3)"/>
    
    <xsl:value-of select="floor($arg1 div $vDenom) + $arg2"/>
  
  </xsl:template>

</xsl:stylesheet>