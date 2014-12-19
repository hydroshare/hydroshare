<!--
===========================================================================
 Stylesheet: iter.xsl       General Iteration of a Function                
    Version: 1.0 (2002-03-16)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->
<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 exclude-result-prefixes="xsl ext">

<!--
===========================================================================
       this implements functional power composition,                       
       that is f(f(...f(x)))))...)                                         
                                                                           
       f composed with itself n - 1 times                                  
                                                                           
       The corresponding Haskell code is:                                  
        > iter :: (Ord a, Num a) => a -> (b -> b) -> b -> b                
        > iter n f                                                         
        >    | n > 0     = f . iter (n-1) f                                
        >    | otherwise = id                                              
===========================================================================-->
<!--
    Template: iter                                                           
     Purpose: Iterate (compose a function with itself) N times               
  Parameters:-                                                               
    $pTimes - [optional] number of times to iterate                          
    $pFun   - a template reference to the function that's to be iterated     
    $pX     - an initial argument to the function                            
  ========================================================================== -->
  <xsl:template name="iter">
    <xsl:param name="pTimes" select="0"/>
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pX" />
    
    <xsl:choose>
      <xsl:when test="$pTimes = 0" >
        <xsl:copy-of select="$pX"/>
      </xsl:when>
      <xsl:when test="$pTimes = 1">
        <xsl:apply-templates select="$pFun">
          <xsl:with-param name="arg1" select="$pX"/>
          </xsl:apply-templates>
      </xsl:when>
      <xsl:when test="$pTimes > 1">
        <xsl:variable name="vHalfTimes" select="floor($pTimes div 2)"/>
        <xsl:variable name="vHalfIters">
          <xsl:call-template name="iter">
            <xsl:with-param name="pTimes" select="$vHalfTimes"/>
		    <xsl:with-param name="pFun" select="$pFun"/>
		    <xsl:with-param name="pX" select="$pX"/>
          </xsl:call-template>
        </xsl:variable>
          
        <xsl:call-template name="iter">
          <xsl:with-param name="pTimes" select="$pTimes - $vHalfTimes"/>
		      <xsl:with-param name="pFun" select="$pFun"/>
		      <xsl:with-param name="pX" select="ext:node-set($vHalfIters)"/>
        </xsl:call-template>
      </xsl:when>
      <xsl:otherwise>
        <xsl:message>[iter]Error: the $pTimes argument must be
                      a positive integer or 0.
        </xsl:message>
      </xsl:otherwise>
    </xsl:choose>
    
  </xsl:template>

<!--
===========================================================================
       This is a variation of the iter function.                           
       Iterations are performed only while the predicate p                 
       is true on the argument of the iteration                            
===========================================================================-->
<!--
    Template: iterUntil                                                      
     Purpose: Iterate (compose a function with itself)                       
              until a condition is satisfied                                 
  Parameters:-                                                               
    $pCond  - a template reference to a predicate that tests                 
              the iteration stop-condition. Returns 0 or 1                   
    $pFun   - a template reference to the function that's to be iterated     
    $arg1   - an initial argument to the function                            
  ========================================================================== -->
   <xsl:template name="iterUntil">
    <xsl:param name="pCond" select="/.."/>
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="arg1" select="/.."/>
    
    <xsl:variable name="vCond">
      <xsl:apply-templates select="$pCond">
        <xsl:with-param name="arg1" select="$arg1"/>
      </xsl:apply-templates>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="$vCond = 1" >
        <xsl:copy-of select="$arg1"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vrtfFunResult">
            <xsl:apply-templates select="$pFun">
              <xsl:with-param name="arg1" select="$arg1"/>
            </xsl:apply-templates>
        </xsl:variable>
        
        <xsl:call-template name="iterUntil">
          <xsl:with-param name="pCond" select="$pCond"/>
          <xsl:with-param name="pFun" select="$pFun"/>
          <xsl:with-param name="arg1"
                 select="ext:node-set($vrtfFunResult)/node()"/>
        </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
<!--
  This template implements the scanIter function                            
  defined in Haskell as:                                                    
                                                                            
  > scanIter :: (Ord a, Num a) => a -> (b -> b) -> b -> [b]                 
  > scanIter n f x                                                          
  >    | n == 0  = [x]                                                      
  >    | n > 0   = result ++ [f(last result)]                               
  >                  where result = scanIter (n-1) f x                      
  ==========================================================================-->

  
<!--
    Template: scanIter                                                      
     Purpose: Iterate (compose a function with itself) N times              
              and produce a list, whose elements are the results            
              from the partial iterations                                   
  Parameters:-                                                              
    $arg1   - the number of times to iterate                                
    $arg2   - a template reference to the function that's to be iterated    
    $arg3   - an initial argument to the function                           
    $arg4   - [optional] name for the elements in the result node-set       
  ==========================================================================-->
  <xsl:template name="scanIter">
    <xsl:param name="arg1"/>               <!-- n -->
    <xsl:param name="arg2" select="/.."/>  <!-- f -->
    <xsl:param name="arg3"/>               <!-- x -->
    <xsl:param name="arg4" select="'el'"/> <!-- elName -->
    
    <xsl:choose>
     <xsl:when test="$arg1 &lt; 0">
       <xsl:message>[scanIter]Error: Negative value for n.</xsl:message>
     </xsl:when>
     <xsl:when test="$arg1 = 0">
       <xsl:element name="{$arg4}">
	       <xsl:value-of select="$arg3"/>
       </xsl:element>
     </xsl:when>
     <xsl:otherwise>
       <xsl:variable name="vrtfIterMinus">
         <xsl:call-template name="scanIter">
           <xsl:with-param name="arg1" select="$arg1 - 1"/>
           <xsl:with-param name="arg2" select="$arg2"/>
           <xsl:with-param name="arg3" select="$arg3"/>
           <xsl:with-param name="arg4" select="$arg4"/>
         </xsl:call-template>
       </xsl:variable>
       
       <xsl:variable name="vIterMinus" 
                     select="ext:node-set($vrtfIterMinus)/*"/>
       
       <xsl:variable name="vrtfLastIter">
         <xsl:element name="{$arg4}">
	         <xsl:apply-templates select="$arg2">
	           <xsl:with-param name="arg1" select="$vIterMinus[last()]"/>
	         </xsl:apply-templates>
         </xsl:element>
       </xsl:variable>
       
         <xsl:copy-of select="$vIterMinus"/>
         <xsl:copy-of select="ext:node-set($vrtfLastIter)"/>
     </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>