<!--
===========================================================================
 Stylesheet: exp.xsl                                                       
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
 xmlns:fCondInInterval="f:fCondInInterval"
 xmlns:fScaleByE="f:fScaleByE"
 xmlns:x="f:x-exp.xsl"
 exclude-result-prefixes="xsl x ext fCondInInterval fScaleByE"
>

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->
   <xsl:import href="iter.xsl"/>
   
<!--
      Template: exp                                                          
      Purpose : Return the value of e^X                                      
    Parameters:                                                              
    $pX       - the real value X, to be used as the "power" in e^X           
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
   <xsl:template name="exp">
     <xsl:param name="pX"/>
     <xsl:param name="pEps" select=".00000001"/>
     
     <xsl:variable name="vResult">
	     <xsl:call-template name="expIter">
	       <xsl:with-param name="pX" select="$pX"/>
	       <xsl:with-param name="pRslt" select="1 + $pX"/>
	       <xsl:with-param name="pElem" select="$pX"/>
	       <xsl:with-param name="pN" select="1"/>
	       <xsl:with-param name="pEps" select="$pEps"/>
	     </xsl:call-template>
     </xsl:variable>
	     
     <xsl:choose>
       <xsl:when test="$vResult >= 0">
         <xsl:value-of select="$vResult"/>
       </xsl:when>
       <xsl:otherwise>0</xsl:otherwise>
     </xsl:choose>

   </xsl:template>
   
   <xsl:template name="expIter">
       <xsl:param name="pX"/>
       <xsl:param name="pRslt"/>
       <xsl:param name="pElem"/>
       <xsl:param name="pN"/>
       <xsl:param name="pEps"/>
       
       <xsl:variable name="vnextN" select="$pN+1"/>
       
       <xsl:variable name="vnewElem" 
                select="$pElem*$pX div $vnextN"/>
                
       <xsl:variable name="vnewResult" select="$pRslt + $vnewElem"/>
       
       <xsl:variable name="vdiffResult" select="$vnewResult - $pRslt"/>
       <xsl:choose>
         <xsl:when test="$vdiffResult > $pEps or $vdiffResult &lt; -$pEps">
			     <xsl:call-template name="expIter">
			       <xsl:with-param name="pX" select="$pX"/>
			       <xsl:with-param name="pRslt" select="$vnewResult"/>
			       <xsl:with-param name="pElem" select="$vnewElem"/>
			       <xsl:with-param name="pN" select="$vnextN"/>
			       <xsl:with-param name="pEps" select="$pEps"/>
			     </xsl:call-template>
         </xsl:when>
         <xsl:otherwise>
           <xsl:value-of select="$vnewResult"/>
         </xsl:otherwise>
       </xsl:choose>
   </xsl:template>

<!--
      Template: ln                                                           
      Purpose : Return the value of ln(X)                                    
    Parameters:                                                              
    $pX       - the real value X, to be used in calculating ln(X)            
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
   <xsl:template name="ln">
     <xsl:param name="pX"/>
     <xsl:param name="pEps" select=".00000001"/>
     
     <xsl:if test="not($pX > 0)">
       <xsl:message terminate="yes">
         <xsl:value-of
         select="concat('[Error]ln: non-positive argument passed:',
                        $pX)"/>
       </xsl:message>
     </xsl:if>
     
     <xsl:variable name="vrtfReduceArg">
       <cnt>0</cnt>
       <x><xsl:value-of select="$pX"/></x>
     </xsl:variable>
     
     <xsl:variable name="vCondInInterval"
                   select="$x:st/fCondInInterval:*[1]"/>
     <xsl:variable name="vScaleByE"
                   select="$x:st/fScaleByE:*[1]"/>

     <xsl:variable name="vrtfScaledArg">
         <xsl:call-template name="iterUntil">
           <xsl:with-param name="pCond" select="$vCondInInterval"/>
           <xsl:with-param name="pFun" select="$vScaleByE"/>
           <xsl:with-param name="arg1"
                           select="ext:node-set($vrtfReduceArg)/*"/>
         </xsl:call-template>
     </xsl:variable>
     
     <xsl:variable name="vIntTerm"
     select="ext:node-set($vrtfScaledArg)/cnt"/>

     <xsl:variable name="vFracTerm"
     select="ext:node-set($vrtfScaledArg)/x"/>

     <xsl:variable name="vPartResult">
         <xsl:call-template name="lnIter">
           <xsl:with-param name="pX" select="$vFracTerm - 1"/>
           <xsl:with-param name="pRslt" select="$vFracTerm - 1"/>
           <xsl:with-param name="pElem" select="$vFracTerm - 1"/>
           <xsl:with-param name="pN" select="1"/>
           <xsl:with-param name="pEps" select="$pEps"/>
         </xsl:call-template>
     </xsl:variable>
     
     <xsl:value-of select="$vIntTerm + $vPartResult"/>
   </xsl:template>
   
<!--
      Template: log                                                          
      Purpose : Return the value of log(base, X)                             
                (the logarithm of X using base base)                         
    Parameters:                                                              
    $pX       - the real value X, to be used in calculating log(base, X)     
    $pBase    - [optional] the value for the base of the logarithm (10)      
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
   <xsl:template name="log">
     <xsl:param name="pX"/>
     <xsl:param name="pBase" select="10"/>
     <xsl:param name="pEps" select=".00000001"/>
     
     <xsl:if test="not($pBase > 0 and $pBase != 1)">
       <xsl:message terminate="yes">
         <xsl:value-of select="concat('[Error]log: Invalid log base: ',
                                      $pBase
                                      )"/>
       </xsl:message>
     </xsl:if>
     
     <xsl:variable name="vLogBase">
       <xsl:call-template name="ln">
         <xsl:with-param name="pX" select="$pBase"/>
         <xsl:with-param name="pEps" select="$pEps"/>
       </xsl:call-template>
     </xsl:variable>
     
     <xsl:variable name="vLnX">
       <xsl:call-template name="ln">
         <xsl:with-param name="pX" select="$pX"/>
         <xsl:with-param name="pEps" select="$pEps"/>
       </xsl:call-template>
     </xsl:variable>
     
     <xsl:value-of select="$vLnX div $vLogBase"/>
   </xsl:template>

<!--
      Template: log10                                                        
      Purpose : Return the value of the decimal logarithm of X               
                (the logarithm of X using base 10)                           
    Parameters:                                                              
    $pX       - the real value X, to be used in calculating log10(X)         
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
   <xsl:template name="log10">
     <xsl:param name="pX"/>
     <xsl:param name="pEps" select=".00000001"/>
	   
	   <xsl:call-template name="log">
	     <xsl:with-param name="pX" select="$pX"/>
	     <xsl:with-param name="pBase" select="10"/>
       <xsl:with-param name="pEps" select="$pEps"/>
	   </xsl:call-template>
	 </xsl:template>

<!--
      Template: log2                                                         
      Purpose : Return the value of the binary logarithm of X                
                (the logarithm of X using base 2)                            
    Parameters:                                                              
    $pX       - the real value X, to be used in calculating log2(X)          
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
   <xsl:template name="log2">
     <xsl:param name="pX"/>
     <xsl:param name="pEps" select=".00000001"/>
	   
	   <xsl:call-template name="log">
	     <xsl:with-param name="pX" select="$pX"/>
	     <xsl:with-param name="pBase" select="2"/>
       <xsl:with-param name="pEps" select="$pEps"/>
	   </xsl:call-template>
	 </xsl:template>
	 
<!--
      Template: pow                                                          
      Purpose : Return the value of base^X (base to the power of X)          
    Parameters:                                                              
    $pBase    - the value for the base                                       
    $pPower   - the real value X, to be used in calculating base^X           
    $pEps     - [optional] accuracy required                                 
                increase the number of decimal places for greater accuracy   
                but at the expense of performance.                           
  ========================================================================== -->
	 <xsl:template name="pow">
	   <xsl:param name="pBase"/>
	   <xsl:param name="pPower"/>
     <xsl:param name="pEps" select=".00000001"/>
     
     <xsl:if test="not($pBase > 0)">
       <xsl:message terminate="yes">
         <xsl:value-of select="concat('[Error]pow: Non-positive pow base: ',
                                      $pBase
                                      )"/>
       </xsl:message>
     </xsl:if>
     
     <xsl:variable name="vLogBase">
       <xsl:call-template name="ln">
         <xsl:with-param name="pX" select="$pBase"/>
         <xsl:with-param name="pEps" select="$pEps"/>
       </xsl:call-template>
     </xsl:variable>
     
     <xsl:call-template name="exp">
       <xsl:with-param name="pX" select="$vLogBase * $pPower"/>
       <xsl:with-param name="pEps" select="$pEps"/>
     </xsl:call-template>
	 </xsl:template>
   
  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
   <xsl:variable name="vE" select="2.71828182845904"/>
   <xsl:variable name="x:st" select="document('')/*"/>

   <fCondInInterval:fCondInInterval/>
   <fScaleByE:fScaleByE/>

   <xsl:template name="lnIter">
       <xsl:param name="pX"/>
       <xsl:param name="pRslt"/>
       <xsl:param name="pElem"/>
       <xsl:param name="pN"/>
       <xsl:param name="pEps"/>

       <xsl:variable name="vnextN" select="$pN+1"/>

       <xsl:variable name="vnewElem" select="-$pElem*$pX"/>

       <xsl:variable name="vnewResult"
                     select="$pRslt + $vnewElem div $vnextN"/>

       <xsl:variable name="vdiffResult" select="$vnewResult - $pRslt"/>
       <xsl:choose>
         <xsl:when test="$vdiffResult > $pEps or $vdiffResult &lt; -$pEps">
			     <xsl:call-template name="lnIter">
			       <xsl:with-param name="pX" select="$pX"/>
			       <xsl:with-param name="pRslt" select="$vnewResult"/>
			       <xsl:with-param name="pElem" select="$vnewElem"/>
			       <xsl:with-param name="pN" select="$vnextN"/>
			       <xsl:with-param name="pEps" select="$pEps"/>
			     </xsl:call-template>
         </xsl:when>
         <xsl:otherwise>
           <xsl:value-of select="$vnewResult"/>
         </xsl:otherwise>
       </xsl:choose>
   </xsl:template>

   <xsl:template match="fCondInInterval:*">
     <xsl:param name="arg1" select="/.."/>
     
     <xsl:variable name="vX" select="number($arg1[name()='x'])"/>
     
     <xsl:choose>
       <xsl:when test="$vX >= 0.5 and $vX &lt;= 1.5">1</xsl:when>
       <xsl:otherwise>0</xsl:otherwise>
     </xsl:choose>
   </xsl:template>
   
   <xsl:template match="fScaleByE:*">
     <xsl:param name="arg1" select="/.."/>

     <xsl:variable name="vCnt" select="number($arg1[name()='cnt'])"/>
     <xsl:variable name="vX" select="number($arg1[name()='x'])"/>
     
     <xsl:choose>
       <xsl:when test="$vX > 1.5">
         <cnt><xsl:value-of select="$vCnt + 1"/></cnt>
         <x><xsl:value-of select="$vX div $vE"/></x>
       </xsl:when>
       <xsl:otherwise>
         <cnt><xsl:value-of select="$vCnt - 1"/></cnt>
         <x><xsl:value-of select="$vX * $vE"/></x>
       </xsl:otherwise>
     </xsl:choose>
   </xsl:template>
   
</xsl:stylesheet>