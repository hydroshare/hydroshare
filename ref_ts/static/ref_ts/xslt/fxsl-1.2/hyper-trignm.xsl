<!--
===========================================================================
 Stylesheet: hyper-trignm.xsl.                                             
    Version: 1.0 (2002-03-24)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
===========================================================================-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:htrigSin="f:htrigSin" xmlns:htrigCos="f:htrigCos"
  xmlns:htrigTan="f:htrigTan" xmlns:htrigCot="f:htrigCot"
  xmlns:htrigSec="f:htrigSec" xmlns:htrigCsc="f:htrigCsc"
  xmlns:x="f:hyper-trignm.xsl"
  exclude-result-prefixes="xsl htrigSin htrigCos htrigTan htrigCot htrigSec htrigCsc">
  
  <xsl:import href="sqrt.xsl"/>

<!--
  ==========================================================================
    Module Interface:                                                       
  ========================================================================== -->


  <!--
    Template: hsin                                                           
     Purpose: Return the hyperbolic sine of X                                
  Parameters:-                                                               
    $pX    - the angle (specified in radians or degrees - see $pUnit)        
    $pUnit - [optional] the unit of the given angle £pX                      
             specify 'deg' for degrees or                                    
                     'rad' for radians (default)                             
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="hsin">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigSin:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: hcos                                                          
     Purpose: Return the hyperbolic cosine of X                             
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="hcos">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigCos:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: htan                                                          
     Purpose: Return the hyperbolic tangent of X                            
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="htan">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigTan:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: hcot                                                          
     Purpose: Return the hyperbolic cotangent of X                          
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="hcot">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigCot:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: hsec                                                          
     Purpose: Return the hyperbolic secant of X                             
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="hsec">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigSec:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: hcsc                                                          
     Purpose: Return the hyperbolic cosecant of X                           
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="hcsc">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_htrigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/htrigCsc:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!-- defined constant for pi -->
  <xsl:variable name="pi" select="3.1415926535897"/>

  <!-- ************************************************************* -->
  <!-- ********************* INTERNAL USE ONLY ********************* -->
  <!-- ************************************************************* -->
  <!-- defined constants -->
  <xsl:variable name="deg2rads" select="$pi div 180"/>
  <!-- internal use only - for applying functions from central _trigWrapper -->
  <htrigSin:htrigSin/>
  <htrigCos:htrigCos/>
  <htrigTan:htrigTan/>
  <htrigCot:htrigCot/>
  <htrigSec:htrigSec/>
  <htrigCsc:htrigCsc/>
  <xsl:variable name="x:vstTop" select="document('')/*"/>

  <!-- internally used templates -->
  <xsl:template name="_htrigWrapper">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <!-- convert degrees to radians (when 'deg' specified) -->
    <xsl:variable name="vRads" select="(($pUnit = 'rad') * $pX) + ((not($pUnit = 'rad')) * ($pX * $deg2rads))"/>
    <!-- apply the appropriate function -->
    <xsl:apply-templates select="$pFun">
      <xsl:with-param name="pX" select="$vRads"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:apply-templates>
  </xsl:template>

  <xsl:template name="_hsin" match="htrigSin:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>

    <xsl:call-template name="_hsineIter">
      <xsl:with-param name="pX2" select="$pX*$pX"/>
      <xsl:with-param name="pRslt" select="$pX"/>
      <xsl:with-param name="pElem" select="$pX"/>
      <xsl:with-param name="pN" select="1"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_hsineIter">
    <xsl:param name="pX2"/>
    <xsl:param name="pRslt"/>
    <xsl:param name="pElem"/>
    <xsl:param name="pN"/>
    <xsl:param name="pEps"/>
    <xsl:variable name="vnextN" select="$pN+2"/>
    <xsl:variable name="vnewElem" select="$pElem*$pX2 div ($vnextN*($vnextN - 1))"/>
    <xsl:variable name="vnewResult" select="$pRslt + $vnewElem"/>
    <xsl:variable name="vdiffResult" select="$vnewResult - $pRslt"/>
    <xsl:choose>
      <xsl:when test="$vdiffResult > $pEps or $vdiffResult &lt; -$pEps">
        <xsl:call-template name="_hsineIter">
          <xsl:with-param name="pX2" select="$pX2"/>
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

  <xsl:template name="_hcos" match="htrigCos:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    
    <xsl:variable name="vhsin">
	    <xsl:call-template name="_hsin">
	      <xsl:with-param name="pX" select="$pX"/>
	      <xsl:with-param name="pEps" select="$pEps"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:call-template name="sqrt">
      <xsl:with-param name="N" select="1 + $vhsin * $vhsin"/>
      <xsl:with-param name="Eps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_htan" match="htrigTan:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>

    <xsl:variable name="vhSin">
      <xsl:call-template name="_hsin">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="pEps" select="$pEps"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:variable name="vhCos">
      <xsl:call-template name="_hcos">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="pEps" select="$pEps"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="$vhSin div $vhCos"/>
  </xsl:template>

  <xsl:template name="_hcot" match="htrigCot:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:variable name="vhTan">
      <xsl:call-template name="_htan">
        <xsl:with-param name="pX" select="$pX"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$vhTan = 'Infinity'">0</xsl:when>
      <xsl:when test="-$pEps &lt; $vhTan and $vhTan &lt; $pEps">
        <xsl:message terminate="yes">
          <xsl:value-of select="concat('[Error]hcot() not defined for x=',$pX)"/>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="1 div $vhTan"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_hsec" match="htrigSec:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:variable name="vhCos">
      <xsl:call-template name="_hcos">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="pEps" select="$pEps"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:value-of select="1 div $vhCos"/>
  </xsl:template>

  <xsl:template name="_hcsc" match="htrigCsc:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    
    <xsl:variable name="vhSin">
	    <xsl:call-template name="_hsin">
	      <xsl:with-param name="pX" select="$pX"/>
	      <xsl:with-param name="pEps" select="$pEps"/>
	    </xsl:call-template>
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="-$pEps &lt; $vhSin and $vhSin &lt; $pEps">
        <xsl:message terminate="yes">[Error]hcsc not defined for ~~ 0</xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="1 div $vhSin"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>