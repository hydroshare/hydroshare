<xsl:stylesheet version="1.0" 
 xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
 xmlns:ext="http://exslt.org/common"
 xmlns:curryPartialApplicator="f:curryPartialApplicator"
 exclude-result-prefixes="ext curryPartialApplicator"
 >
 
  <xsl:template name="curry">
    <xsl:param name="pFun" select="/.."/>
    <xsl:param name="pNargs" select="2"/>
    <xsl:param name="pStripAuxNamespace"/>
    <xsl:param name="args" select="/.."/>
    <xsl:param name="arg1" select="/.."/>
    <xsl:param name="arg2" select="/.."/>
    <xsl:param name="arg3" select="/.."/>
    <xsl:param name="arg4" select="/.."/>
    <xsl:param name="arg5" select="/.."/>
    <xsl:param name="arg6" select="/.."/>
    <xsl:param name="arg7" select="/.."/>
    <xsl:param name="arg8" select="/.."/>
    <xsl:param name="arg9" select="/.."/>
    <xsl:param name="arg10" select="/.."/>
    
    <xsl:if test="$pNargs &lt; 2">
      <xsl:message terminate="yes">
         [curry]Error: pNargs (number of arguments) of a fn to be 
                       curried must be at least 2
      </xsl:message>
    </xsl:if>
    
    <xsl:if test="$pNargs > 10">
      <xsl:message terminate="yes">
         [curry]Error: pNargs (number of arguments) of a fn to be 
                       curried must not exceed 10
      </xsl:message>
    </xsl:if>
    
    <!-- Build the Resulting fn with an empty Arguments store -->
    <xsl:variable name="vrtfCurriedNoArgs">
	    <curryPartialApplicator:curryPartialApplicator>
		    <fun><xsl:copy-of select="$pFun"/></fun>
		    <curryNumargs><xsl:value-of select="$pNargs"/></curryNumargs>
		    <curryStrip><xsl:value-of select="$pStripAuxNamespace"/></curryStrip>
	    </curryPartialApplicator:curryPartialApplicator>
    </xsl:variable>
    
    <xsl:variable name="vCurriedNoArgs" 
                  select="ext:node-set($vrtfCurriedNoArgs)/*"/>
    
    <xsl:choose>
      <xsl:when test="not($args)
                    and 
                      not($arg1 or $arg2 or $arg3 or $arg4 or $arg5   
                       or $arg6 or $arg7 or $arg8 or $arg9 or $arg10   
                          )">
        <xsl:copy-of select="$vCurriedNoArgs"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:apply-templates select="$vCurriedNoArgs">
			    <xsl:with-param name="args" select="$args"/>
			    <xsl:with-param name="arg1" select="$arg1"/>
			    <xsl:with-param name="arg2" select="$arg2"/>
			    <xsl:with-param name="arg3" select="$arg3"/>
			    <xsl:with-param name="arg4" select="$arg4"/>
			    <xsl:with-param name="arg5" select="$arg5"/>
			    <xsl:with-param name="arg6" select="$arg6"/>
			    <xsl:with-param name="arg7" select="$arg7"/>
			    <xsl:with-param name="arg8" select="$arg8"/>
			    <xsl:with-param name="arg9" select="$arg9"/>
			    <xsl:with-param name="arg10" select="$arg10"/>
        
        </xsl:apply-templates>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template match="curryPartialApplicator:*">
    <xsl:param name="args" select="/.."/>
    <xsl:param name="arg1" select="/.."/>
    <xsl:param name="arg2" select="/.."/>
    <xsl:param name="arg3" select="/.."/>
    <xsl:param name="arg4" select="/.."/>
    <xsl:param name="arg5" select="/.."/>
    <xsl:param name="arg6" select="/.."/>
    <xsl:param name="arg7" select="/.."/>
    <xsl:param name="arg8" select="/.."/>
    <xsl:param name="arg9" select="/.."/>
    <xsl:param name="arg10" select="/.."/>
    
    <xsl:if test="not($args)
                  and 
                    not($arg1 or $arg2 or $arg3 or $arg4 or $arg5   
                     or $arg6 or $arg7 or $arg8 or $arg9 or $arg10   
                        )">
      <xsl:message terminate="yes">
         [currying]Error: No arguments specified!      
      </xsl:message>
    </xsl:if>
    
    <xsl:variable name="vrtvArgs">
	  <xsl:copy-of select="$args"/>
	  <xsl:if test="$arg1">
	    <arg1>
	      <xsl:copy-of select="$arg1"/>
	    </arg1>
	  </xsl:if>
	  <xsl:if test="$arg2">
	    <arg2>
	      <xsl:copy-of select="$arg2"/>
	    </arg2>
	  </xsl:if>
	  <xsl:if test="$arg3">
	    <arg3>
	      <xsl:copy-of select="$arg3"/>
	    </arg3>
	  </xsl:if>
	  <xsl:if test="$arg4">
	    <arg4>
	      <xsl:copy-of select="$arg4"/>
	    </arg4>
	  </xsl:if>
	  <xsl:if test="$arg5">
	    <arg5>
	      <xsl:copy-of select="$arg5"/>
	    </arg5>
	  </xsl:if>
	  <xsl:if test="$arg6">
	    <arg6>
	      <xsl:copy-of select="$arg6"/>
	    </arg6>
	  </xsl:if>
	  <xsl:if test="$arg7">
	    <arg7>
	      <xsl:copy-of select="$arg7"/>
	    </arg7>
	  </xsl:if>
	  <xsl:if test="$arg8">
	    <arg8>
	      <xsl:copy-of select="$arg8"/>
	    </arg8>
	  </xsl:if>
	  <xsl:if test="$arg9">
	    <arg9>
	      <xsl:copy-of select="$arg9"/>
	    </arg9>
	  </xsl:if>
	  <xsl:if test="$arg10">
	    <arg10>
	      <xsl:copy-of select="$arg10"/>
	    </arg10>
	  </xsl:if>
    </xsl:variable>
    
    <xsl:variable name="vArgs" select="ext:node-set($vrtvArgs)/*"/>
    
    <xsl:if test="count($vArgs) > curryNumargs">
      <xsl:message>
        <xsl:value-of select="concat('[currying]Error: The number of actual arguments supplied is ',
                                      count($vArgs), ' -- bigger than the number of arguments of this function:',
                                      curryNumargs
                                     )"/>
      </xsl:message>
    </xsl:if>
    
    <xsl:if test="$vArgs = curryArgs/*">
      <xsl:message>[currying]Error: Same argument(s) fixed twice</xsl:message>
    </xsl:if>
    
    <xsl:for-each select="$vArgs[not(position()=last())]">
      <xsl:variable name="vThisPosition" select="position()"/>
      <xsl:if test=". = $vArgs[position() > $vThisPosition
                             and
                               name() = name(current())
                               ]">
        <xsl:message>[currying]Error: Same argument(s) specified twice</xsl:message>
      </xsl:if>
    </xsl:for-each>
    
    <!-- Normal  Processing -->
    <xsl:variable name="vrtfNewFun">
	  <curryPartialApplicator:curryPartialApplicator>
	    <xsl:copy-of select="fun"/>
	    <xsl:copy-of select="curryStrip"/>
	    <xsl:copy-of select="curryNumargs"/>
	    <curryArgs>
	      <xsl:copy-of select="curryArgs/*"/>
	      <xsl:copy-of select="$vArgs"/>
	    </curryArgs>
	  </curryPartialApplicator:curryPartialApplicator>
    </xsl:variable>
    
    <xsl:variable name="vNewFun" select="ext:node-set($vrtfNewFun)/*"/>

    <xsl:choose>
      <xsl:when test="curryNumargs > count($vNewFun/curryArgs/*)">
        <xsl:copy-of select="$vNewFun"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:choose>
          <xsl:when test="not(string(curryStrip))">
		        <xsl:apply-templates select="fun/*[1]">
		          <xsl:with-param name="arg1"
		                          select="$vNewFun/curryArgs/arg1/node()"/>
		          <xsl:with-param name="arg2"
		                          select="$vNewFun/curryArgs/arg2/node()"/>
		          <xsl:with-param name="arg3"
		                          select="$vNewFun/curryArgs/arg3/node()"/>
		          <xsl:with-param name="arg4"
		                          select="$vNewFun/curryArgs/arg4/node()"/>
		          <xsl:with-param name="arg5"
		                          select="$vNewFun/curryArgs/arg5/node()"/>
		          <xsl:with-param name="arg6"
		                          select="$vNewFun/curryArgs/arg6/node()"/>
		          <xsl:with-param name="arg7"
		                          select="$vNewFun/curryArgs/arg7/node()"/>
		          <xsl:with-param name="arg8"
		                          select="$vNewFun/curryArgs/arg8/node()"/>
		          <xsl:with-param name="arg9"
		                          select="$vNewFun/curryArgs/arg9/node()"/>
		          <xsl:with-param name="arg10"
		                          select="$vNewFun/curryArgs/arg10/node()"/>
		        </xsl:apply-templates>
	        </xsl:when>
	        <xsl:otherwise>
	          <xsl:variable name="vrtf-strippedArgs">
	            <xsl:apply-templates select="$vNewFun/curryArgs/*" 
	                                 mode="stripNamespace"/>
	          </xsl:variable>
	          
	          <xsl:variable name="vstrippedArgs" 
	               select="ext:node-set($vrtf-strippedArgs)"/>
	          
		        <xsl:apply-templates select="fun/*[1]">
		          <xsl:with-param name="arg1"
		                          select="$vstrippedArgs/arg1/node()"/>
		          <xsl:with-param name="arg2"
		                          select="$vstrippedArgs/arg2/node()"/>
		          <xsl:with-param name="arg3"
		                          select="$vstrippedArgs/arg3/node()"/>
		          <xsl:with-param name="arg4"
		                          select="$vstrippedArgs/arg4/node()"/>
		          <xsl:with-param name="arg5"
		                          select="$vstrippedArgs/arg5/node()"/>
		          <xsl:with-param name="arg6"
		                          select="$vstrippedArgs/arg6/node()"/>
		          <xsl:with-param name="arg7"
		                          select="$vstrippedArgs/arg7/node()"/>
		          <xsl:with-param name="arg8"
		                          select="$vstrippedArgs/arg8/node()"/>
		          <xsl:with-param name="arg9"
		                          select="$vstrippedArgs/arg9/node()"/>
		          <xsl:with-param name="arg10"
		                          select="$vstrippedArgs/arg10/node()"/>
		        </xsl:apply-templates>
	          
	        </xsl:otherwise>
        </xsl:choose>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <xsl:template match="node()" mode="stripNamespace">
    <xsl:choose>
      <xsl:when test="self::*">
		    <xsl:element name="{name()}">
		      <xsl:copy-of select="namespace::*[name() != 'curryPartialApplicator']"/>
		      <xsl:copy-of select="@*"/>
		      <xsl:apply-templates select="node()" 
		                           mode="stripNamespace"/>
		    </xsl:element>
	    </xsl:when>
	    <xsl:otherwise>
	      <xsl:copy-of select="."/>
	    </xsl:otherwise>
    </xsl:choose>
  
  </xsl:template>
</xsl:stylesheet>