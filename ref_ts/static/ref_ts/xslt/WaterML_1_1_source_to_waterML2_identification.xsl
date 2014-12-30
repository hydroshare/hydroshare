<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:wml2="http://www.opengis.net/waterml/2.0" xmlns:gml="http://www.opengis.net/gml/3.2"
    xmlns:om="http://www.opengis.net/om/2.0" xmlns:xlink="http://www.w3.org/1999/xlink"
    xmlns:wml="http://www.cuahsi.org/waterML/1.1/" xmlns:fn="http://www.w3.org/2005/xpath-functions"
    xsi:schemaLocation="http://www.opengis.net/waterml/2.0 http://schemas.opengis.net/waterml/2.0/waterml2.xsd"
    xmlns:gco="http://www.isotc211.org/2005/gco" xmlns:gss="http://www.isotc211.org/2005/gss"
    xmlns:gmd="http://www.isotc211.org/2005/gmd">
    <!-- 
        <source sourceID="3">
        <sourceCode>3</sourceCode>
        <organization>Utah State University Utah Water Research Laboratory</organization>
        <sourceDescription>Water chemistry monitoring data collected by Utah State University as part of a National Science Foundation funded test bed project.</sourceDescription>
        <contactInformation>
        <contactName>Amber Spackman</contactName>
        <typeOfContact>main</typeOfContact>
        <email>amber.s@aggiemail.usu.edu</email>
        <phone>1-435-797-0045</phone>
        <address xsi:type="xsd:string">8200 Old Main Hill
        ,Logan, Utah 84322-8200</address>
        </contactInformation>
        <sourceLink>http://water.usu.edu/littlebearriver</sourceLink>
        <citation>Water chemistry monitoring data collected by Jeff Horsburgh, David Stevens, David Tarboton, Nancy Mesner, Amber Spackman, and Sandra Gurrero at Utah State University as part of a National Science Foundation funded WATERS Network Test Bed project.</citation>
        </source>
    -->
    <xsl:template match="wml:timeSeriesResponse">
        <!-- /default:timeSeriesResponse/default:timeSeries[1]/default:values[1]/default:source[1] -->
        <wml2:ObservationMetadata>
            <xsl:call-template name="identificationInfo">
                <xsl:with-param name="source" select="wml:timeSeries/wml:values/wml:source"/>

            </xsl:call-template>
        </wml2:ObservationMetadata>
    </xsl:template>

    <xsl:template name="sourceToMetadata">
        <xsl:param name="sources"></xsl:param>
        
        <!-- this will need to be contact from HIS central -->
        <gmd:contact gco:nilReason="inapplicable"/>
        
        <xsl:call-template name="gmdDateStamp"/>
        <gmd:locale>
            <gmd:PT_Locale>
                <gmd:languageCode>
                    <gmd:LanguageCode codeList="LanguageCode" codeListValue="EN-US">English-United States</gmd:LanguageCode>
                </gmd:languageCode>
                <gmd:characterEncoding>
                    <gmd:MD_CharacterSetCode codeList="MD_CharacterSetCode" codeListValue="utf8">UTF 8</gmd:MD_CharacterSetCode>
                </gmd:characterEncoding>
            </gmd:PT_Locale>
        </gmd:locale>
        <xsl:for-each select="$sources">
            <xsl:call-template name="identificationInfo">

                <xsl:with-param name="source" select="."/>

            </xsl:call-template>
        </xsl:for-each>
      
        
    </xsl:template>

    <xsl:template name="gmdDateStamp">
        <gmd:dateStamp gco:nilReason="inapplicable"/>
        <!--   <gmd:dateStamp> <gco:DateTime>2006-05-04T18:13:51.0Z</gco:DateTime> </gmd:dateStamp> -->
       
    </xsl:template>

    <xsl:template name="CI_ResponsibleParty">
        <xsl:param name="source">
            <xsl:value-of select="."/>
        </xsl:param>


        
            <gmd:CI_ResponsibleParty>
                <gmd:individualName>
                    <gmd:LocalisedCharacterString locale="#EN-US">
                        <xsl:value-of select="$source/wml:contactInformation/wml:contactName"/>
                    </gmd:LocalisedCharacterString>
                </gmd:individualName>


                <gmd:organisationName>
                    <gmd:LocalisedCharacterString locale="#EN-US">
                        <xsl:value-of select="$source/wml:organization"/>
                    </gmd:LocalisedCharacterString>
                </gmd:organisationName>
                <!--        <gmd:positionName gco:nilReason="inapplicable">
                    <gmd:Country codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">Country5</gmd:Country>
                </gmd:positionName>
                -->
                <gmd:contactInfo>
                    <gmd:CI_Contact>
                        <gmd:phone>
                            <gmd:CI_Telephone>
                                <gmd:voice>
                                    <gco:CharacterString>
                                        <xsl:value-of
                                            select="$source/wml:contactInformation/wml:phone"/>
                                    </gco:CharacterString>
                                </gmd:voice>
                            </gmd:CI_Telephone>
                        </gmd:phone>
                        <gmd:address>
                            <gmd:CI_Address>
                                <gmd:deliveryPoint>
                                    <gco:CharacterString>
                                        <xsl:value-of
                                            select="$source/wml:contactInformation/wml:address"/>
                                    </gco:CharacterString>
                                </gmd:deliveryPoint>
                                <gmd:electronicMailAddress>
                                    <gco:CharacterString>
                                        <xsl:value-of
                                            select="$source/wml:contactInformation/wml:email"/>
                                    </gco:CharacterString>
                                </gmd:electronicMailAddress>
                            </gmd:CI_Address>
                        </gmd:address>

                        <gmd:onlineResource>
                            <gmd:CI_OnlineResource>
                                <gmd:linkage>
                                    <gmd:URL>
                                        <xsl:value-of select="$source/wml:sourceLink"/>
                                    </gmd:URL>
                                </gmd:linkage>
                            </gmd:CI_OnlineResource>

                        </gmd:onlineResource>
                    </gmd:CI_Contact>
                </gmd:contactInfo>
                <gmd:role>
                    <gmd:CI_RoleCode codeList="ISOTC211/19115"
                        codeSpace="http://www.isotc211.org/2005/resources/Codelist/gmxCodelists.xml#CI_RoleCode">
                        <xsl:attribute name="codeListValue">principalInvestigator<!--      <xsl:value-of select="$source/wml:contactInformation/wml:typeOfContact"
                            /> --></xsl:attribute>
                    </gmd:CI_RoleCode>
                </gmd:role>
            </gmd:CI_ResponsibleParty>
        

    </xsl:template>

    <xsl:template name="identificationInfo">
        <xsl:param name="source">
            <xsl:value-of select="."/>
        </xsl:param>





        <gmd:identificationInfo>
            <gmd:MD_DataIdentification>
                <xsl:attribute name="id"> <xsl:value-of select="generate-id( $source/wml:sourceCode)"/></xsl:attribute>
                <gmd:citation>
                    <gmd:CI_Citation>
                        <gmd:title>
                            <gco:CharacterString>
                                <xsl:value-of select="$source/wml:citation"/>
                            </gco:CharacterString>
                        </gmd:title>

                        <gmd:date gco:nilReason="inapplicable"/>
                        <!--    <gmd:date>    <gmd:CI_Date >
                                <gmd:date     />
                              <gmd:date >
                                    <gco:DateTime>2006-05-04T18:13:51.0Z</gco:DateTime>
                                </gmd:date>
                               
                                <gmd:dateType >
                                    <gmd:CI_DateTypeCode codeList="ISO" codeListValue="ISO" codeSpace="ISO"></gmd:CI_DateTypeCode>
                                </gmd:dateType>
                            </gmd:CI_Date>
                        </gmd:date>
                         -->
                    </gmd:CI_Citation>
                </gmd:citation>
                <gmd:abstract>
                    <gco:CharacterString>
                        <xsl:value-of select="$source/wml:sourceDescription"/>
                    </gco:CharacterString>
                </gmd:abstract>
              
                <!-- purpose, status -->
                <gmd:pointOfContact>
                    <xsl:call-template name="CI_ResponsibleParty">
                        
                        <xsl:with-param name="source" select="."/>
                        
                    </xsl:call-template>
                </gmd:pointOfContact>  
                <gmd:language>
                    <gco:CharacterString>EN-US</gco:CharacterString>
                </gmd:language>
            </gmd:MD_DataIdentification>
            
        </gmd:identificationInfo>
        <!--    <gmd:distributionInfo >
                <xsl:attribute name="xlink:href"> </xsl:attribute>
            </gmd:distributionInfo>
          -->
    </xsl:template>
    <!--           <gmd:identificationInfo xlink:type="simple" xlink:href="http://www.oxygenxml.com/" xlink:role="http://www.oxygenxml.com/" xlink:arcrole="http://www.oxygenxml.com/"
        xlink:title="title271" xlink:show="new" xlink:actuate="onLoad" uuidref="uuidref175"
        gco:nilReason="inapplicable">
        <gmd:MD_DataIdentification id="ID222" uuid="uuid165">
        <gmd:citation xlink:type="simple" xlink:href="http://www.oxygenxml.com/" xlink:role="http://www.oxygenxml.com/" xlink:arcrole="http://www.oxygenxml.com/"
        xlink:title="title272" xlink:show="new" xlink:actuate="onLoad" uuidref="uuidref176"
        gco:nilReason="inapplicable">
        <gmd:CI_Citation id="ID223" uuid="uuid166">
        <gmd:title gco:nilReason="inapplicable">
        <gmd:MD_ProgressCode codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">MD_ProgressCode7</gmd:MD_ProgressCode>
        </gmd:title>
        <gmd:date xlink:type="simple" xlink:href="http://www.oxygenxml.com/" xlink:role="http://www.oxygenxml.com/" xlink:arcrole="http://www.oxygenxml.com/"
        xlink:title="title273" xlink:show="new" xlink:actuate="onLoad" uuidref="uuidref177"
        gco:nilReason="inapplicable">
        <gmd:CI_Date id="ID224" uuid="uuid167">
        <gmd:date gco:nilReason="inapplicable">
        <gco:Date>2006-05-04</gco:Date>
        </gmd:date>
        <gmd:dateType gco:nilReason="inapplicable">
        <gmd:CI_DateTypeCode codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">CI_DateTypeCode52</gmd:CI_DateTypeCode>
        </gmd:dateType>
        </gmd:CI_Date>
        </gmd:date>
        <gmd:date xlink:type="simple" xlink:href="http://www.oxygenxml.com/" xlink:role="http://www.oxygenxml.com/" xlink:arcrole="http://www.oxygenxml.com/"
        xlink:title="title274" xlink:show="new" xlink:actuate="onLoad" uuidref="uuidref178"
        gco:nilReason="inapplicable">
        <gmd:CI_Date id="ID225" uuid="uuid168">
        <gmd:date gco:nilReason="inapplicable">
        <gco:DateTime>2006-05-04T18:13:51.0Z</gco:DateTime>
        </gmd:date>
        <gmd:dateType gco:nilReason="inapplicable">
        <gmd:CI_DateTypeCode codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">CI_DateTypeCode53</gmd:CI_DateTypeCode>
        </gmd:dateType>
        </gmd:CI_Date>
        </gmd:date>
        </gmd:CI_Citation>
        </gmd:citation>
        <gmd:abstract gco:nilReason="inapplicable">
        <gmd:MD_ImagingConditionCode codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">MD_ImagingConditionCode4</gmd:MD_ImagingConditionCode>
        </gmd:abstract>
        <gmd:language gco:nilReason="inapplicable">
        <gmd:MD_DistributionUnits codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">MD_DistributionUnits1</gmd:MD_DistributionUnits>
        </gmd:language>
        <gmd:language gco:nilReason="inapplicable">
        <gmd:Country codeList="http://www.oxygenxml.com/" codeListValue="http://www.oxygenxml.com/" codeSpace="http://www.oxygenxml.com/">Country8</gmd:Country>
        </gmd:language>
        </gmd:MD_DataIdentification>
        </gmd:identificationInfo> -->
</xsl:stylesheet>
