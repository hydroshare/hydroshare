<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:x="f:fxsl-monteCarlo"
 xmlns:genTest="f:genTest" 
 xmlns:rFloat="f:rFloat"
 exclude-result-prefixes="xsl ext x 
                          genTest rFloat"
 >
 
  <xsl:import href="random.xsl"/>
  <xsl:import href="iter.xsl"/>
  
  <!-- Fun: GenerateAndTest -->
  <genTest:genTest/>  
  <!-- Fun: rFloat -->
  <rFloat:rFloat/>    
  
  <xsl:variable name="x:st" 
                select="document('')/*"/>
  
  <xsl:template name="monteCarlo">
    <!-- n (Iterations) -->
    <xsl:param name="arg1" select="1"/>
    <!-- f (fn to be integrated) -->
    <xsl:param name="arg2" select="/.."/>   
    <!-- sx (start of interval for x) -->
    <xsl:param name="arg3"/>                
    <!-- tx (end of interval for x) -->
    <xsl:param name="arg4"/>                
    <!-- sy (start of interval for y) -->
    <xsl:param name="arg5" select="'0'"/>   
    <!-- ty (end of interval for y) -->
    <xsl:param name="arg6"/>                
    <!-- starting seed -->
    <xsl:param name="arg7" select="$seed"/> 
    
    <xsl:variable name="vGenAndTest" 
                  select="$x:st/genTest:*[1]"/>
    <xsl:variable name="vRFloat" 
                  select="$x:st/rFloat:*[1]"/>
    
    <xsl:variable name="vIntRange" 
                  select="$modulus - 1"/>
    
<!-- rndFloatX = rFloat((tx - sx)/dintRange) sx -->
    <xsl:variable name="vrtf-rndFloatX">
      <xsl:call-template name="curry">
        <xsl:with-param name="pNargs" 
                        select="3"/>
        <xsl:with-param name="pFun" 
                        select="$vRFloat"/>
        <xsl:with-param name="arg1" 
             select="($arg4 - $arg3) 
                    div $vIntRange"/>
        <xsl:with-param name="arg2" 
                        select="$arg3"/>
      </xsl:call-template>
    </xsl:variable>
    
<!-- rndFloatY = rFloat((ty - sy)
                    / dintRange) sy -->
    <xsl:variable name="vrtf-rndFloatY">
      <xsl:call-template name="curry">
        <xsl:with-param name="pNargs" 
                        select="3"/>
        <xsl:with-param name="pFun" 
                        select="$vRFloat"/>
        <xsl:with-param name="arg1" 
             select="($arg6 - $arg5) 
                    div $vIntRange"/>
        <xsl:with-param name="arg2" 
                        select="$arg5"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vrtfGTParams">
	   <cnt>0</cnt>
	   <seed>
	     <xsl:value-of select="$arg7"/>
       </seed>
    </xsl:variable>
    
    <xsl:variable name="vrtf-GenerateAndTest">
      <xsl:call-template name="curry">
        <xsl:with-param name="pNargs" 
                        select="4"/>
        <xsl:with-param name="pFun" 
                        select="$vGenAndTest"/>
        <xsl:with-param name="arg2" 
         select="ext:node-set($vrtf-rndFloatX)/*"/>
        <xsl:with-param name="arg3" 
         select="ext:node-set($vrtf-rndFloatY)/*"/>
        <!-- f --> 
        <xsl:with-param name="arg4" 
                        select="$arg2"/> 
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vResultIterations">
      <xsl:call-template name="iter">
        <xsl:with-param name="pTimes" 
                        select="$arg1"/>
        <xsl:with-param name="pFun" 
   select="ext:node-set($vrtf-GenerateAndTest)/*"/>
        <xsl:with-param name="pX" 
         select="ext:node-set($vrtfGTParams)/*"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="vnHits" 
      select="ext:node-set($vResultIterations)/*[1]"/>
    
    <xsl:variable name="vSpace" 
         select="($arg4 - $arg3) * ($arg6 - $arg5)"/>
    
    <xsl:value-of 
         select="$vnHits div $arg1 * $vSpace"/>
  </xsl:template>
  
  <xsl:template match="genTest:*">
    <!-- (ct, sd) -->
    <xsl:param name="arg1" select="/.."/> 
    <!-- rndFloatX -->
    <xsl:param name="arg2" select="/.."/> 
    <!-- rndFloatY -->
    <xsl:param name="arg3" select="/.."/> 
    <!-- f -->
    <xsl:param name="arg4" select="/.."/> 
    
    <xsl:variable name="vCount" 
                  select="$arg1[1]"/>
    <xsl:variable name="vSeed"  
                  select="$arg1[2]"/>
    
    <xsl:variable name="vNextSeed">
      <xsl:call-template name="randNext">
        <xsl:with-param name="arg1" 
                        select="$vSeed"/>
      </xsl:call-template>
    </xsl:variable>
    
    <xsl:variable name="v-rndX">
      <xsl:apply-templates select="$arg2">
        <xsl:with-param name="arg3" 
                        select="$vSeed"/>
      </xsl:apply-templates> 
    </xsl:variable>
    
    <xsl:variable name="vF-rndX">
      <xsl:apply-templates select="$arg4">
        <xsl:with-param name="arg1" 
                        select="$v-rndX"/>
      </xsl:apply-templates>
    </xsl:variable>
    
    <xsl:variable name="v-rndY">
      <xsl:apply-templates select="$arg3">
        <xsl:with-param name="arg3" 
                        select="$vNextSeed"/>
      </xsl:apply-templates> 
    </xsl:variable>
    
    <xsl:choose>
      <xsl:when test="$vF-rndX >= $v-rndY">
        <cnt>
         <xsl:value-of select="$vCount + 1"/>
        </cnt>
      </xsl:when>
      <xsl:otherwise>
        <cnt>
         <xsl:value-of select="$vCount"/>
        </cnt>
      </xsl:otherwise>
    </xsl:choose>
	      <seed>
	       <xsl:value-of select="$vNextSeed"/>
	      </seed>
    
  </xsl:template>
  
  <!-- computes a*sd + b -->
  <xsl:template match="rFloat:*"> 
    <xsl:param name="arg1"/> <!-- a -->
    <xsl:param name="arg2"/> <!-- b -->
    <xsl:param name="arg3"/> <!-- sd -->
    
    <xsl:value-of select="$arg1*$arg3 + $arg2"/>
    
  </xsl:template>
</xsl:stylesheet>