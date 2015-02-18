<!--
===========================================================================
 Stylesheet: arcTrignm.xsl       INVERSE  TRIGONOMETRIC  FUNCTIONS         
    Version: 1.0 (2002-03-14)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->
<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:mySinFun="f:mySinFun"
 xmlns:mySinFunPrim="f:mySinFunPrim" 
 xmlns:myTanFun="f:myTanFun"
 xmlns:myTanFunPrim="f:myTanFunPrim" 
 xmlns:myCotFun="f:myCotFun"
 xmlns:myCotFunPrim="f:myCotFunPrim" 
 xmlns:atrigSin="f:atrigSin" xmlns:atrigCos="f:atrigCos"
 xmlns:atrigTan="f:atrigTan" xmlns:atrigCot="f:atrigCot"
 xmlns:atrigSec="f:atrigSec" xmlns:atrigCsc="f:atrigCsc"
 xmlns:x="f:arcTrignm.xsl"
 exclude-result-prefixes=
 "xsl x ext mySinFun mySinFunPrim myTanFun myTanFunPrim myCotFun 
  myCotFunPrim atrigSin atrigCos atrigTan atrigCot atrigSec atrigCsc"
 >

<!--
  ==========================================================================
    Imported files:                                                       
  ========================================================================== -->

  <xsl:import href="findRoot.xsl"/>
  <xsl:import href="trignm.xsl"/>
  <xsl:import href="curry.xsl"/>

<!--
  ==========================================================================
    Module Interface:                                                       
  ========================================================================== -->

<!--
    Template: arcsin                                                         
     Purpose: Return the angle, whose sine value is X                        
  Parameters:-                                                               
    $pX    - a value in the interval [-1, 1]                                 
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arcsin">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigSin:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: arccos                                                         
     Purpose: Return the angle, whose cosine value is X                      
  Parameters:-                                                               
    $pX    - a value in the interval [-1, 1]                                 
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arccos">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigCos:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: arctan                                                         
     Purpose: Return the angle, whose tangens value is X                     
  Parameters:-                                                               
    $pX    - any real value                                                  
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arctan">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigTan:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: arccot                                                         
     Purpose: Return the angle, whose cotangens value is X                   
  Parameters:-                                                               
    $pX    - any real value                                                  
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arccot">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigCot:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: arcsec                                                         
     Purpose: Return the angle, whose secant value is X                      
  Parameters:-                                                               
    $pX    - any real value not belonging to the interval (-1, 1)            
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arcsec">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigSec:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

<!--
    Template: arccsc                                                         
     Purpose: Return the angle, whose cosecant value is X                    
  Parameters:-                                                               
    $pX    - any real value not belonging to the interval (-1, 1)            
    $pUnit - [optional] the unit in which                                    
             the result is to be returned                                    
             specify: 'deg' for degrees or                                   
                      'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="arccsc">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select="0.0000001"/>

     <xsl:call-template name="_atrigWrapper">
      <xsl:with-param name="pFun" select="$x:vst/atrigCsc:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
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
  <atrigSin:atrigSin/>
  <atrigCos:atrigCos/>
  <atrigTan:atrigTan/>
  <atrigCot:atrigCot/>
  <atrigSec:atrigSec/>
  <atrigCsc:atrigCsc/>
  <!-- internal use only - for applying the functions:               
      sin(y) - x                                                     
      cos(y)                                                         
-->
  <mySinFun:mySinFun/>
  <mySinFunPrim:mySinFunPrim/>

  <!-- internal use only - for applying the functions:               
      tan(y) - x                                                     
      tan'(y)                                                         
-->
  <myTanFun:myTanFun/>
  <myTanFunPrim:myTanFunPrim/>
  
  <!-- internal use only - for applying the functions:               
      cot(y) - x                                                     
      cot'(y)                                                         
-->
  <myCotFun:myCotFun/>
  <myCotFunPrim:myTanFunPrim/>


  <!-- internally used templates -->
  <xsl:template name="_atrigWrapper">
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
    
  <xsl:template name="_arcsin" match="atrigSin:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="not(-1 &lt;= $pX and $pX &lt;= 1)">
      <xsl:message terminate="yes">
        [Error]: arcSine argument must be within the interval [-1, 1]
      </xsl:message>
    </xsl:if>
    
    <xsl:choose>
      <xsl:when test="$pX = 0">0</xsl:when>
      <xsl:when test="$pX &lt; -0.99999999">
        <xsl:value-of select="3*$halfPi"/>
      </xsl:when>
      <xsl:otherwise>
		    <xsl:variable name="vSinFun" select="$x:vst/mySinFun:*[1]"/>
		    <xsl:variable name="vCoSFun" select="$x:vst/mySinFunPrim:*[1]"/>
		    
		    <xsl:variable name="vrtf-curriedSinFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vSinFun"/>
		        <xsl:with-param name="pNargs" select="3"/>
		        <xsl:with-param name="arg2" select="$pX"/><!-- pC -->
		        <xsl:with-param name="arg3" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrtf-curriedCoSFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vCoSFun"/>
		        <xsl:with-param name="pNargs" select="2"/>
		        <xsl:with-param name="arg2" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:call-template name="findRootNR">
		      <xsl:with-param name="pFun" select="ext:node-set($vrtf-curriedSinFun)/*"/>
		      <xsl:with-param name="pFunPrim" select="ext:node-set($vrtf-curriedCoSFun)/*"/>
		      <xsl:with-param name="pX0" select="$pi div 6"/>
		      <xsl:with-param name="pEps" select="0.0000001"/>
	      </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="_arccos" match="atrigCos:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
	    
	  <xsl:variable name="vArcSin">
      <xsl:call-template name="_arcsin">
  	    <xsl:with-param name="pX" select="$pX"/>
  	    <xsl:with-param name="pEps" select="$pEps"/>
  	  </xsl:call-template>
    </xsl:variable>
	    
	  <xsl:value-of select="$halfPi - $vArcSin"/>
  </xsl:template>
    
  <xsl:template name="_arctan" match="atrigTan:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:choose>
	    <xsl:when test="$pX > 43 or $pX &lt; -43">
	      <xsl:call-template name="_arccot">
	        <xsl:with-param name="pX" select="1 div $pX"/>
	        <xsl:with-param name="pEps" select="$pEps"/>
	      </xsl:call-template>
	    </xsl:when>
	    <xsl:otherwise>
		    <xsl:variable name="vTanFun" select="$x:vst/myTanFun:*[1]"/>
		    <xsl:variable name="vTanPrFun" select="$x:vst/myTanFunPrim:*[1]"/>
		    
		    <xsl:variable name="vrtf-curriedTanFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vTanFun"/>
		        <xsl:with-param name="pNargs" select="3"/>
		        <xsl:with-param name="arg2" select="$pX"/><!-- pC -->
		        <xsl:with-param name="arg3" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrtf-curriedTanPrFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vTanPrFun"/>
		        <xsl:with-param name="pNargs" select="2"/>
		        <xsl:with-param name="arg2" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrawRoot">
			    <xsl:call-template name="findRootNR">
			      <xsl:with-param name="pFun" select="ext:node-set($vrtf-curriedTanFun)/*"/>
			      <xsl:with-param name="pFunPrim" select="ext:node-set($vrtf-curriedTanPrFun)/*"/>
			      <xsl:with-param name="pX0" select="3"/>
			      <xsl:with-param name="pEps" select="0.0000001"/>
		      </xsl:call-template>
	      </xsl:variable>
		      
	      <xsl:call-template name="_cutIntervals">
	        <xsl:with-param name="pLength" select="$pi"/>
	        <xsl:with-param name="pX" select="$vrawRoot"/>
	      </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_arccot" match="atrigCot:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:choose>
	    <xsl:when test="$pX > 43 or $pX &lt; -43">
	      <xsl:call-template name="_arctan">
	        <xsl:with-param name="pX" select="1 div $pX"/>
	        <xsl:with-param name="pEps" select="$pEps"/>
	      </xsl:call-template>
	    </xsl:when>
      <xsl:when test="$pX = 0">
        <xsl:value-of select="$halfPi"/>
      </xsl:when>
      <xsl:otherwise>
		    <xsl:variable name="vCotFun" select="$x:vst/myCotFun:*[1]"/>
		    <xsl:variable name="vCotPrFun" select="$x:vst/myCotFunPrim:*[1]"/>
		    
		    <xsl:variable name="vrtf-curriedCotFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vCotFun"/>
		        <xsl:with-param name="pNargs" select="3"/>
		        <xsl:with-param name="arg2" select="$pX"/><!-- pC -->
		        <xsl:with-param name="arg3" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrtf-curriedCotPrFun">
		      <xsl:call-template name="curry">
		        <xsl:with-param name="pFun" select="$vCotPrFun"/>
		        <xsl:with-param name="pNargs" select="2"/>
		        <xsl:with-param name="arg2" select="$pEps"/>
		      </xsl:call-template>
		    </xsl:variable>
		    
		    <xsl:variable name="vrawRoot">
			    <xsl:call-template name="findRootNR">
			      <xsl:with-param name="pFun" select="ext:node-set($vrtf-curriedCotFun)/*"/>
			      <xsl:with-param name="pFunPrim" select="ext:node-set($vrtf-curriedCotPrFun)/*"/>
			      <xsl:with-param name="pX0" select="3"/>
			      <xsl:with-param name="pEps" select="0.0000001"/>
		      </xsl:call-template>
	      </xsl:variable>
		      
	      <xsl:call-template name="_cutIntervals">
	        <xsl:with-param name="pLength" select="$pi"/>
	        <xsl:with-param name="pX" select="$vrawRoot"/>
	      </xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template name="_arcsec" match="atrigSec:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="$pX = 0">
      <xsl:message terminate="yes">
        [Error]arcsec: The argument cannot be 0.
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_arccos">
      <xsl:with-param name="pX" select="1 div $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_arccsc" match="atrigCsc:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select="0.0000001"/>
    
    <xsl:if test="$pX = 0">
      <xsl:message terminate="yes">
        [Error]arccsc: The argument cannot be 0.
      </xsl:message>
    </xsl:if>
    
    <xsl:call-template name="_arcsin">
      <xsl:with-param name="pX" select="1 div $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!-- this calculates sin(x) - C -->
  <xsl:template match="mySinFun:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pC -->
    <xsl:param name="arg3"/> <!-- pEps -->
    
    <xsl:variable name="vSineX">
      <xsl:call-template name="sin">
        <xsl:with-param name="pX" select="$arg1"/>
        <xsl:with-param name="pEps" select="$arg3"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vSineX - $arg2"/>
  </xsl:template>

  <xsl:template match="mySinFunPrim:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pEps -->
    
    <xsl:call-template name="cos">
      <xsl:with-param name="pX" select="$arg1"/>
      <xsl:with-param name="pEps" select="$arg2"/>
    </xsl:call-template>
  </xsl:template>
  
    <!-- this calculates tan(x) - C -->
  <xsl:template match="myTanFun:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pC -->
    <xsl:param name="arg3"/> <!-- pEps -->
    
    <xsl:variable name="vTanX">
      <xsl:call-template name="tan">
        <xsl:with-param name="pX" select="$arg1"/>
        <xsl:with-param name="pEps" select="$arg3"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vTanX - $arg2"/>
  </xsl:template>

    <!-- this calculates tan'(x) = sec^2(x) -->
  <xsl:template match="myTanFunPrim:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pEps -->
    
      <xsl:variable name="vSec">
	      <xsl:call-template name="sec">
	        <xsl:with-param name="pX" select="$arg1"/>
	        <xsl:with-param name="pEps" select="$arg2"/>
	      </xsl:call-template>
      </xsl:variable>
      
      <xsl:value-of select="$vSec * $vSec"/>
  </xsl:template>

    <!-- this calculates cot(x) - C -->
  <xsl:template match="myCotFun:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pC -->
    <xsl:param name="arg3"/> <!-- pEps -->
    
    <xsl:variable name="vCotX">
      <xsl:call-template name="cot">
        <xsl:with-param name="pX" select="$arg1"/>
        <xsl:with-param name="pEps" select="$arg3"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="$vCotX - $arg2"/>
  </xsl:template>

    <!-- this calculates cot'(x) = -csc^2(x) -->
  <xsl:template match="myCotFunPrim:*">
    <xsl:param name="arg1"/> <!-- pX -->
    <xsl:param name="arg2"/> <!-- pEps -->
    
      <xsl:variable name="vCsc">
	      <xsl:call-template name="csc">
	        <xsl:with-param name="pX" select="$arg1"/>
	        <xsl:with-param name="pEps" select="$arg2"/>
	      </xsl:call-template>
      </xsl:variable>
      
      <xsl:value-of select="-$vCsc * $vCsc"/>
  </xsl:template>

</xsl:stylesheet>