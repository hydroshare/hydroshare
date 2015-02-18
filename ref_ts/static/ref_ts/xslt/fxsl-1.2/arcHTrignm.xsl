<!--
===========================================================================
 Stylesheet: arcTrignm.xsl    INVERSE  HYPERBOLIC TRIGONOMETRIC  FUNCTIONS 
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
 xmlns:myhSinFun="f:myhSinFun"
 xmlns:myhSinFunPrim="f:myhSinFunPrim" 
 xmlns:myhTanFun="f:myhTanFun"
 xmlns:myhTanFunPrim="f:myhTanFunPrim" 
 xmlns:myhCotFun="f:myhCotFun"
 xmlns:myhCotFunPrim="f:myhCotFunPrim" 
 xmlns:atrighSin="f:atrighSin" xmlns:atrighCos="f:atrighCos"
 xmlns:atrighTan="f:atrighTan" xmlns:atrighCot="f:atrighCot"
 xmlns:atrighSec="f:atrighSec" xmlns:atrighCsc="f:atrighCsc"
 xmlns:x="f:arcHTrignm.xsl"
 exclude-result-prefixes=
 "xsl x ext myhSinFun myhSinFunPrim myhTanFun myhTanFunPrim myhCotFun 
  myhCotFunPrim atrighSin atrighCos atrighTan atrighCot atrighSec atrighCsc"
 >

<!--
  ==========================================================================
    Imported files:                                                         
  ==========================================================================-->

  <xsl:import href="findRoot.xsl"/>
  <xsl:import href="hyper-trignm.xsl"/>
  <xsl:import href="curry.xsl"/>

<!--
  ==========================================================================
    Module Interface:                                                       
  ==========================================================================-->

<!--
    Template: archsin                                                        
     Purpose: Return the angle, whose huperboli csine value is X             
  Parameters:-                                                               
    $pX    - any real number                                                 
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archsin">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighSin:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: archcos                                                        
     Purpose: Return the angle, whose hyperbolic cosine value is X           
  Parameters:-                                                               
    $pX    - a value in the interval [1, +Infinity)                          
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archcos">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighCos:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: archtan                                                        
     Purpose: Return the angle, whose hyperbolic tangens value is X          
  Parameters:-                                                               
    $pX    - any value in [-1, 1]                                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archtan">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighTan:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: archcot                                                        
     Purpose: Return the angle, whose hyperbolic cotangens value is X        
  Parameters:-                                                               
    $pX    - any real value x < -1 or x > 1                                                 
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archcot">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighCot:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: archsec                                                        
     Purpose: Return the angle, whose hyperbolic secant value is X           
  Parameters:-                                                               
    $pX    - any real value not belonging to the interval (0, 1]             
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archsec">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighSec:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: archcsc                                                        
     Purpose: Return the angle, whose hyperbolic cosecant value is X         
  Parameters:-                                                               
    $pX    - any real value x != 0                                           
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="archcsc">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrighWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrighCsc:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
  <xsl:variable name="x:vst" select="document('')/*"/>
  <xsl:variable name="rad2degs" select="180 div $pi"/>

  <!-- internal use only - for applying functions from central _trigWrapper -->
  <atrighSin:atrighSin/>
  <atrighCos:atrighCos/>
  <atrighTan:atrighTan/>
  <atrighCot:atrighCot/>
  <atrighSec:atrighSec/>
  <atrighCsc:atrighCsc/>
  <!-- internal use only - for applying the functions:               
      hsin(y) - x                                                     
      hcos(y)                                                         
-->
  <myhSinFun:myhSinFun/>
  <myhSinFunPrim:myhSinFunPrim/>

  <!-- internal use only - for applying the functions:               
      htan(y) - x                                                     
      htan'(y)                                                         
-->
  <myhTanFun:myhTanFun/>
  <myhTanFunPrim:myhTanFunPrim/>
  
  <!-- internal use only - for applying the functions:               
      hcot(y) - x                                                     
      hcot'(y)                                                         
-->
  <myhCotFun:myhCotFun/>
  <myhCotFunPrim:myhCotFunPrim/>


  <!-- internally used templates -->
  <xsl:template name="_atrighWrapper">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <!-- apply the appropriate function -->
    <xsl:variable name="vradResult">
      <xsl:apply-templates select="$pFun">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="pEps" select="$pEps"/>
      </xsl:apply-templates>
    </xsl:variable>
    <!-- convert radians to degrees (when 'deg' specified) -->
    <xsl:value-of select="(($pUnit = 'rad') * $vradResult)
                  + ((not($pUnit = 'rad')) * ($vradResult * $rad2degs))"/>

  </xsl:template>
    
  <xsl:template name="_archsin" match="atrighSin:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:choose>
      <xsl:when test="$pX = 0">0</xsl:when>
      <xsl:otherwise>
		    <xsl:variable name="vhSinFun" select="$x:vst/myhSinFun:*[1]"/>
		    <xsl:variable name="vhCoSFun" select="$x:vst/myhSinFunPrim:*[1]"/>
		    
		    <xsl:variable name="vrtf-curriedhSinFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vhSinFun"/>
		        <xsl:with-param name="pNargs" select="3"/>
		        <xsl:with-param name="arg2" select="$pX"/><!-- pC -->
		        <xsl:with-param name="arg3" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrtf-curriedhCoSFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vhCoSFun"/>
		        <xsl:with-param name="pNargs" select="2"/>
		        <xsl:with-param name="arg2" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:call-template name="findRootNR">
		      <xsl:with-param name="pFun" select="ext:node-set($vrtf-curriedhSinFun)/*"/>
		      <xsl:with-param name="pFunPrim" select="ext:node-set($vrtf-curriedhCoSFun)/*"/>
		      <xsl:with-param name="pX0" select="$pi div 6"/>
		      <xsl:with-param name="pEps" select="$pEps"/>
	      </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="_archcos" match="atrighCos:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <!-- hcos^2(x) - hsin^2(x) = 1        
                                          
      ==> hsin(x) = sqrt(hcos^2(x) - 1)   
                                          
      ==> x = archsin(sqrt(hcos^2(x) - 1))
-->  
	  <xsl:variable name="vhSin">
      <xsl:call-template name="sqrt">
  	    <xsl:with-param name="N" select="$pX * $pX - 1"/>
  	    <xsl:with-param name="Eps" select="$pEps"/>
  	  </xsl:call-template>
    </xsl:variable>
	    
	  <xsl:call-template name="_archsin">
	    <xsl:with-param name="pX" select="$vhSin"/>
	    <xsl:with-param name="pEps" select="$pEps"/>
	  </xsl:call-template>
  </xsl:template>
    
  <xsl:template name="_archtan" match="atrighTan:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>

<!--
        hcos^2(x) - hsin^2(x) = 1           
   ==>  1 - htan^2(x) = 1/hcos^2(x)         
   ==>  hcos(x) = sqrt(1/(1 - htan^2(x)))   
   ==>  x = archcos(sqrt(1/(1 - htan^2(x))))
-->    
    <xsl:if test="$pX >= 1 or $pX &lt;= -1">
      <xsl:message terminate="yes">
      [Error]archtan: X is outside the interval (-1, 1)
      </xsl:message>
    </xsl:if>
    
    <xsl:variable name="vhCos">
      <xsl:call-template name="sqrt">
        <xsl:with-param name="N" select="1 div (1 - $pX * $pX)"/>
        <xsl:with-param name="Eps" select="$pEps"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="_archcos">
      <xsl:with-param name="pX" select="$vhCos"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
    
  </xsl:template>

  <xsl:template name="_archcot" match="atrighCot:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="$pX >= -1 and $pX &lt;= 1">
      <xsl:message terminate="yes">
      [Error]archcot: X is must be outside the interval [-1, 1]
      </xsl:message>
    </xsl:if>

    <xsl:call-template name="_archtan">
      <xsl:with-param name="pX" select="1 div $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>
  
  <xsl:template name="_archsec" match="atrighSec:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="$pX &lt;= 0 or $pX > 1">
      <xsl:message terminate="yes">
      [Error]archcot: X is must be in the interval (0, 1]
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_archcos">
      <xsl:with-param name="pX" select="1 div $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_archcsc" match="atrighCsc:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="$pX = 0">
      <xsl:message terminate="yes">
        [Error]arccsc: The argument cannot be 0.
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_archsin">
      <xsl:with-param name="pX" select="1 div $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!-- this calculates hsin(x) - C -->
  <xsl:template match="myhSinFun:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pC -->
    <xsl:param name="arg3"/> <!-- pEps -->
    
    <xsl:variable name="vhSineX">
      <xsl:call-template name="hsin">
        <xsl:with-param name="pX" select="$arg1"/>
        <xsl:with-param name="pEps" select="$arg3"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vhSineX - $arg2"/>
  </xsl:template>

  <xsl:template match="myhSinFunPrim:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pEps -->
    
    <xsl:call-template name="hcos">
      <xsl:with-param name="pX" select="$arg1"/>
      <xsl:with-param name="pEps" select="$arg2"/>
    </xsl:call-template>
  </xsl:template>
  

</xsl:stylesheet>