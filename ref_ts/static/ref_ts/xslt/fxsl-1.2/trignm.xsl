<!--
===========================================================================
 Stylesheet: trignm.xsl.xsl                                                
    Version: 1.0 (2002-03-13)                                              
     Author: Dimitre Novatchev                                             
     Notice: Copyright (c)2002 D.Novatchev  ALL RIGHTS RESERVED.           
             No limitation on use - except this code may not be published, 
             in whole or in part, without prior written consent of the     
             copyright owner.                                              
                                                                           
     Acknowledgements:                                                     
             The documentation to this file, the general documenting style 
             and some efficiency optimisation are work of Martin Rowlinson 
===========================================================================-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:trigSin="f:trigSin" xmlns:trigCos="f:trigCos"
  xmlns:trigTan="f:trigTan" xmlns:trigCot="f:trigCot"
  xmlns:trigSec="f:trigSec" xmlns:trigCsc="f:trigCsc"
  xmlns:x="f:trig_lib.xsl"
  exclude-result-prefixes="xsl trigSin trigCos trigTan trigCot trigSec trigCsc">

<!--
  ==========================================================================
    Module Interface:                                                       
  ========================================================================== -->


  <!--
    Template: sin                                                            
     Purpose: Return the sine of X                                           
  Parameters:-                                                               
    $pX    - the angle (specified in radians or degrees - see $pUnit)        
    $pUnit - [optional] the unit of the given angle £pX                      
             specify 'deg' for degrees or                                    
                     'rad' for radians (default)                             
    $pEps  - [optional] accuracy required                                    
             increase the number of decimal places for greater accuracy but  
             at the expense of performance.                                  
  ========================================================================== -->
  <xsl:template name="sin">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigSin:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: cos                                                           
     Purpose: Return the cosine of X                                        
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="cos">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigCos:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: tan                                                           
     Purpose: Return the tangent of X                                       
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="tan">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigTan:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: cot                                                           
     Purpose: Return the cotangent of X                                     
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="cot">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigCot:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: sec                                                           
     Purpose: Return the secant of X                                        
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="sec">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigSec:*[1]"/>
      <xsl:with-param name="pX" select="$pX"/>
      <xsl:with-param name="pUnit" select="$pUnit"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <!--
  ==========================================================================
    Template: csc                                                           
     Purpose: Return the cosecant of X                                      
  Parameters:-                                                              
    $pX    - the angle (specified in radians or degrees - see $pUnit)       
    $pUnit - [optional] the unit of the given angle £pX                     
             specify 'deg' for degrees or                                   
                     'rad' for radians (default)                            
    $pEps  - [optional] accuracy required                                   
             increase the number of decimal places for greater accuracy but 
             at the expense of performance.                                 
  ==========================================================================-->
  <xsl:template name="csc">
    <xsl:param name="pX"/>
    <xsl:param name="pUnit" select="'rad'"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_trigWrapper">
      <xsl:with-param name="pFun" select="$x:vstTop/trigCsc:*[1]"/>
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
  <xsl:variable name="halfPi" select="$pi div 2"/>
  <xsl:variable name="twicePi" select="$pi*2"/>
  <xsl:variable name="deg2rads" select="$pi div 180"/>
  <!-- internal use only - for applying functions from central _trigWrapper -->
  <trigSin:trigSin/>
  <trigCos:trigCos/>
  <trigTan:trigTan/>
  <trigCot:trigCot/>
  <trigSec:trigSec/>
  <trigCsc:trigCsc/>
  <xsl:variable name="x:vstTop" select="document('')/*"/>

  <!-- internally used templates -->
  <xsl:template name="_trigWrapper">
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

  <xsl:template name="_sin" match="trigSin:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:variable name="pY">
      <xsl:choose>
        <xsl:when test="not(0 &lt;= $pX and $twicePi > $pX)">
          <xsl:call-template name="_cutIntervals">
            <xsl:with-param name="pLength" select="$twicePi"/>
            <xsl:with-param name="pX" select="$pX"/>
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$pX"/>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:call-template name="_sineIter">
      <xsl:with-param name="pX2" select="$pY*$pY"/>
      <xsl:with-param name="pRslt" select="$pY"/>
      <xsl:with-param name="pElem" select="$pY"/>
      <xsl:with-param name="pN" select="1"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_sineIter">
    <xsl:param name="pX2"/>
    <xsl:param name="pRslt"/>
    <xsl:param name="pElem"/>
    <xsl:param name="pN"/>
    <xsl:param name="pEps"/>
    <xsl:variable name="vnextN" select="$pN+2"/>
    <xsl:variable name="vnewElem" select="-$pElem*$pX2 div ($vnextN*($vnextN - 1))"/>
    <xsl:variable name="vnewResult" select="$pRslt + $vnewElem"/>
    <xsl:variable name="vdiffResult" select="$vnewResult - $pRslt"/>
    <xsl:choose>
      <xsl:when test="$vdiffResult > $pEps or $vdiffResult &lt; -$pEps">
        <xsl:call-template name="_sineIter">
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

  <xsl:template name="_cos" match="trigCos:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_sin">
      <xsl:with-param name="pX" select="$halfPi - $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_tan" match="trigTan:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:param name="_pAbort" select="1"/>
    <xsl:variable name="vnumHalfPis" select="floor($pX div $halfPi)"/>
    <xsl:variable name="vdiffHalfPi" select="$pX - $halfPi*$vnumHalfPis"/>
    <xsl:choose>
      <xsl:when test="-$pEps &lt; $vdiffHalfPi and $vdiffHalfPi &lt; $pEps
                      and $vnumHalfPis mod 2 = 1">
        <xsl:choose>
          <xsl:when test="$_pAbort">
            <xsl:message terminate="yes">
              <xsl:value-of select="concat('[Error]tan() not defined for x=',$pX)"/>
            </xsl:message>
          </xsl:when>
          <xsl:otherwise>Infinity</xsl:otherwise>
        </xsl:choose>
      </xsl:when>
      <xsl:otherwise>
        <xsl:variable name="vSin">
          <xsl:call-template name="_sin">
            <xsl:with-param name="pX" select="$pX"/>
            <xsl:with-param name="pEps" select="$pEps"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="vCos">
          <xsl:call-template name="_cos">
            <xsl:with-param name="pX" select="$pX"/>
            <xsl:with-param name="pEps" select="$pEps"/>
          </xsl:call-template>
        </xsl:variable>
        <xsl:value-of select="$vSin div $vCos"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_cot" match="trigCot:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:variable name="vTan">
      <xsl:call-template name="_tan">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="_pAbort" select="0"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="$vTan = 'Infinity'">0</xsl:when>
      <xsl:when test="-$pEps &lt; $vTan and $vTan &lt; $pEps">
        <xsl:message terminate="yes">
          <xsl:value-of select="concat('[Error]cot() not defined for x=',$pX)"/>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="1 div $vTan"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_sec" match="trigSec:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:variable name="vCos">
      <xsl:call-template name="_cos">
        <xsl:with-param name="pX" select="$pX"/>
        <xsl:with-param name="pEps" select="$pEps"/>
      </xsl:call-template>
    </xsl:variable>
    <xsl:choose>
      <xsl:when test="-$pEps &lt; $vCos and $vCos &lt; $pEps">
        <xsl:message terminate="yes">
          <xsl:value-of select="concat('[Error]sec() not defined for x=',$pX)"/>
        </xsl:message>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="1 div $vCos"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="_csc" match="trigCsc:*">
    <xsl:param name="pX"/>
    <xsl:param name="pEps" select=".00000001"/>
    <xsl:call-template name="_sec">
      <xsl:with-param name="pX" select="$halfPi - $pX"/>
      <xsl:with-param name="pEps" select="$pEps"/>
    </xsl:call-template>
  </xsl:template>

  <xsl:template name="_cutIntervals">
    <xsl:param name="pLength"/>
    <xsl:param name="pX"/>
    <xsl:variable name="vsignX">
      <xsl:choose>
        <xsl:when test="$pX >= 0">1</xsl:when>
        <xsl:otherwise>-1</xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="vdiff" select="$pLength*floor($pX div $pLength) -$pX"/>
    <xsl:choose>
      <xsl:when test="$vdiff*$pX > 0">
        <xsl:value-of select="$vsignX*$vdiff"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="-$vsignX*$vdiff"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>