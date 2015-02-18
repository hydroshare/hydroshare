<?xml version="1.0" encoding="utf-8"?>
    
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:hisc="http://hiscentral.cuahsi.org/20100205/" 
    version="1.0"
    >
    <xsl:template name="HisOntologyMapper">
    <xsl:param name="VariableCode"/>   
<!--    http://hiscentral.cuahsi.org//webservices/hiscentral.asmx/GetMappedVariables?conceptids=&Networkids= -->
        <xsl:variable name="hisVar" select="document('../HisControlledVocabularies/GetMappedVariables.xml')//hisc:MappedVariable/hisc:variableCode[text()=$VariableCode]/.."/>
        <xsl:variable name="mappedConcept" select="document('../HisControlledVocabularies/getOntologyTree.xml')//hisc:conceptid[text()=$hisVar/hisc:conceptCode/text()]/../hisc:keyword/text()"/>
<xsl:choose >
    <xsl:when test="$mappedConcept">
        <xsl:value-of select="$mappedConcept"/>
        
    </xsl:when>
    <xsl:otherwise>
        <xsl:text>Unmapped</xsl:text>
    </xsl:otherwise>
</xsl:choose>
    </xsl:template>  
 

 <!--               <xsl:template name="HisOntologyMapper">
                <xsl:param name="VariableCode"/>
                <xsl:choose>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=32359'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62614/DataType=Average'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00052/DataType=Maximum'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00052/DataType=Minimum'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00036/DataType=Median'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00012'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Instantaneous'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63158/DataType=Maximum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63158/DataType=Minimum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63158/statistic=32400'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62611/DataType=Average'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62611/DataType=Maximum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00004'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00005'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31700'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/statistic=31200'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:99065/DataType=Maximum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:99065/DataType=Minimum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Variance'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31800'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00058/DataType=Average'">Discharge, groundwaterflow</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62968/DataType=Maximum'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62968/DataType=Minimum'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62969/DataType=Maximum'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62969/DataType=Minimum'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62609/DataType=Maximum'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62609/DataType=Minimum'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Average'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/DataType=Average'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Maximum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Minimum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Maximum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Minimum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00055/DataType=Maximum'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00055/DataType=Minimum'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00055/DataType=Average'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00045/DataType=Maximum'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/statistic=00012'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00061/DataType=Maximum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00061/DataType=Minimum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00061/DataType=Average'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=30900'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=30800'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00045/DataType=Cumulative'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Average'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Maximum'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Minimum'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Average'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/DataType=Maximum'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/DataType=Minimum'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00301/DataType=Maximum'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00301/DataType=Minimum'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00301/DataType=Average'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/DataType=Median'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/DataType=Average'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00035/DataType=Average'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00036/DataType=Maximum'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00036/DataType=Minimum'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00036/DataType=Average'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:99065/DataType=Average'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Instantaneous'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=30900'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00020/DataType=Maximum'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00020/DataType=Minimum'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00020/DataType=Average'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00045/DataType=Average'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/DataType=Maximum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/DataType=Minimum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00021/DataType=Average'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/DataType=Average'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=32400'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/DataType=Maximum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/DataType=Minimum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00052/DataType=Average'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:75969/DataType=Average'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=32400'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/statistic=32400'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=30800'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00021'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00024'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00025/DataType=Maximum'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00025/DataType=Minimum'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00025/DataType=Average'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/statistic=31200'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Median'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=00009'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Median'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00011/DataType=Maximum'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00011/DataType=Minimum'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00011/DataType=Average'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00011/DataType=Instantaneous'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/DataType=Instantaneous'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31600'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=30700'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31200'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/statistic=31200'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=00005'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62611/DataType=Minimum'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62625/DataType=Maximum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62625/DataType=Minimum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62625/DataType=Average'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=00021'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=00022'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=00023'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=00024'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:82127/DataType=Maximum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:82127/DataType=Minimum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:82127/DataType=Average'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Maximum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Maximum'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Minimum'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Minimum'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Average'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61727/DataType=Average'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61729/DataType=Average'">Wind gust direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62608/DataType=Maximum'">Radiation, incident</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62608/DataType=Minimum'">Radiation, incident</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=31200'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/DataType=Instantaneous'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/statistic=31500'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72019/statistic=30200'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/statistic=30600'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72020/DataType=Instantaneous'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31300'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:46529/DataType=Cumulative'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00400/statistic=00004'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=30600'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00055/DataType=Cumulative'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62609/DataType=Average'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62968/DataType=Average'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62969/DataType=Average'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=31200'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62608/DataType=Average'">Radiation, incident</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:61728/DataType=Maximum'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:99772/DataType=Cumulative'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/DataType=Cumulative'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:72124/DataType=Average'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=31400'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00011/DataType=Median'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62615/statistic=32400'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=30730'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00010/statistic=00004'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00403/statistic=00004'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00403/DataType=Instantaneous'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Instantaneous'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Median'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/DataType=Cumulative'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/DataType=Cumulative'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63160/DataType=Maximum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63160/DataType=Minimum'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:63160/DataType=Average'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:75969/DataType=Maximum'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:75969/DataType=Minimum'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00021/DataType=Maximum'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00021/DataType=Minimum'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62614/statistic=32400'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00036/DataType=Cumulative'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00045/DataType=Median'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00022'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00023'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=00007'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62603/DataType=Maximum'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62603/DataType=Minimum'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:62603/DataType=Average'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00060/statistic=30800'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00065/statistic=30700'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00045/DataType=Minimum'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00035/DataType=Maximum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISDV:00035/DataType=Minimum'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00021'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:34942'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:34961'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:46529'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30292'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:63160'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62845'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:99019'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:99020'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:99065'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:82127'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62464'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:90077'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:49266'">Carbon, total organic</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:35052'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30207'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30208'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30209'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30210'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:30243'">Carbon, total organic</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:34903'">Manganese</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00010'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00011'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00014'">Wet bulb temperature </xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00020'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:50042'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:50050'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:49491'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:49491'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:49701'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62610'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62611'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62614'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:62615'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00301'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00400'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00403'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00035'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00036'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00045'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00052'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00055'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00058'">Discharge, groundwaterflow</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00060'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00061'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00062'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00065'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00072'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00077'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00078'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:00117'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:82300'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:72019'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:72020'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'NWISIID:81026'">Snow water equivalent</xsl:when>
                <xsl:when test="$VariableCode = 'NWISUV:99968'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'NWISUV:00060'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISUV:00065'">Water depth, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NWISUV:75969'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:687-2'">Beryllium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16099-1'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16099-2'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16103-1'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1274-1'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:464-1'">Streptococci, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:428-5'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:462-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:481-1'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:375-2'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:375-1'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:376-1'">Hydrolyzable phopshorus</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:377-1'">Hydrolyzable P plus
                                                  orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:317-2'">Molybdenum</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:317-1'">Molybdenum</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:330-2'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:330-1'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16327-1'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:8-2'">Acrylonitrile</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:8-1'">Acrylonitrile</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:26-2'">Antimony</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:26-1'">Antimony</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:3-1'">Acenaphthylene</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:3-2'">Acenaphthylene</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:595-1'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:51-1'">Beryllium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:51-2'">Beryllium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:74-2'">Cadmium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:74-1'">Cadmium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:139-1'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1-1'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:29-2'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:29-1'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:42-5'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:137-2'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:137-1'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17116-2'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17116-1'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:650-1'">Asbestos</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17118-1'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17118-1'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17118-2'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17118-2'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:9780-1'">Escherichia coli</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:9780-2'">Escherichia coli</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:11737-1'">Coliform, total</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:11737-2'">Coliform, total</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:11739-1'">Enterococci</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:434-1'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:331-2'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:331-1'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:332-1'">Nitrogen, total inorganic </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:335-1'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:335-2'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:336-1'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:336-2'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:233-1'">Flux, evaporation</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17115-1'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:17115-2'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1473-1'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1473-2'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1476-1'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1476-2'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:605-5'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:515-1'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:528-1'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:545-2'">Zinc</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:545-1'">Zinc</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1275-2'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1275-1'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:521-1'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:530-1'">Unspecified</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:380-1'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:436-1'">Unspecified</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1475-2'">Hydrolyzable phopshorus</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1477-1'">Phosphorus, polyphosphate </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1475-1'">Hydrolyzable phopshorus</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:964-1'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:323374-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16329-1'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:201-1'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1732-1'">Clostridium perfringens</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1594-5'">Wet bulb temperature </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:136-1'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:136-1'">Streptococci, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:2-1'">Acenaphthene</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:2-2'">Acenaphthene</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:13-1'">Aldrin</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:13-2'">Aldrin</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:59-1'">Boron</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:59-2'">Boron</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16313-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:389183-1'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:323372-1'">Cyanide</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:16100-1'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:514-1'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:1273-1'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:379-1'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:379-2'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:437-1'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:15841-1'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:7-1'">Acrolein</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:7-2'">Acrolein</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:333-2'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:333-1'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:334-1'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:334-2'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'EPA:217-1'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:217-1'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:217-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:220-1'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:220-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:648-1'">Antimony</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:329-1'">N, albuminoid</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:239-1'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:241-1'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EPA:243-1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:AS'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:BIOSI'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:BOD5W'">Biochemical oxygen demand</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CD'">Cadmium</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CDOM_440'">Solids, fixed dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CDOM_SLOPE'">Radiation, reflected</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CHLA'">Chlorophyll a</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CLW'">Chlorine</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:COD'">Chemical oxygen demand</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CR'">Chromium</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CU'">Copper</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DIN'">Nitrogen, total inorganic </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DOC'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DON'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DOP'">Phosphorus, dissolved organic </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FCOLI_C'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FCOLI_M'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FE_M'">Iron</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FE_U'">Iron</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FLOW_INS'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FS'">Solids, fixed dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:FSS'">Solids, fixed suspended </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:HARDNESS'">Hardness, carbonate</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:HG'">Mercury</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:KD'">Light attenuation coefficient</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NH4F'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NH4W'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO23F'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO23W'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO2F'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO2W'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO3F'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:NO3W'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:ORP'">Oxidation reduction potential</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PB'">Lead</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PC'">Carbon, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PHEO'">Pheophytin</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PIC'">Carbon, suspended inorganic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PIP'">Phosphorus, suspended inorganic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PN'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PO4F'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PO4W'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:POC'">Carbon, suspended organic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PON'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:PP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SALINITY'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SE'">Selenium</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SECCHI'">Secchi depth</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SIF'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CHLAM'">Chlorophyll a</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SIGMA_T'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SIW'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SO4F'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SO4W'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SPCOND'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SSC_%FINE'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:SSC_TOTAL'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TALK'">Carbonate (CO3)</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TCOLI_C'">Coliform, total</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TCOLI_M'">Coliform, total</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TDN'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TDP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TDS'">Solids, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TKNF'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TKNW'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TN'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TOC'">Carbon, total organic</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TON'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TS'">Solids, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TSS'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TURB_FTU'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:TURB_NTU'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:VSS'">Solids, volatile suspended</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:WTEMP'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:ZN'">Zinc</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:DO_SAT_P'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CIMS:CHL_A'">Chlorophyll a</xsl:when>
                <xsl:when test="$VariableCode = 'NWISGW:72019'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU1'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU2'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU3'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU4'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU6'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU7'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU8'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU9'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU10'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU11'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU13'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU14'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU15'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU16'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU17'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU27'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU28'">Phosphorus, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU29'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU30'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU31'">Nitrogen, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU32'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU33'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU34'">Discharge, unspecified</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU19'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU20'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU21'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU22'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU23'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU24'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU25'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ML:USU26'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10001'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10002'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10005'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10006'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10007'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'SDRFP:10008'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'COTC:002'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'COTC:001'">Dry bulb temperature</xsl:when>
                <xsl:when test="$VariableCode = 'COTC:003'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'COTC:004'">Radiation, net shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'COTC:005'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Nitrite_Nitrate'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:TP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Nitrate'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:999002'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:999003'">Soil heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:999004'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:999001'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:639'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:640'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:641'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:642'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:643'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:644'">Ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:645'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'NADP:646'">Chlorine</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:647'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:648'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:649'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:650'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'NADP:651'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Water level'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:516'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:519'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:524'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:526'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:545'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:597'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:598'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:601'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:517'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:520'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:525'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:528'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:529'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:509'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:510'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:511'">Water depth, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:512'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:513'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:514'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:515'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:508'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:533'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:523'">Temperature, 1 meter below water surface</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:543'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:521'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:542'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:592'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:593'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:594'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:595'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SRBHOS:596'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'SabineBio:v60'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SabineBio:bowfin.max'">Amia calva</xsl:when>
                <xsl:when test="$VariableCode = 'SabineBio:bowfin.min'">Amia calva</xsl:when>
                <xsl:when test="$VariableCode = 'SabineBio:v20'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'SabineBio:v80'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU4'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU5'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU6'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU7'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU8'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU9'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU10'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU11'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU12'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU13'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU32'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU33'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU34'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU35'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU36'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU37'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU39'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU40'">Phosphorus, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU41'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU44'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU47'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU48'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU63'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU64'">Nitrogen, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU65'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU14'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU15'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU16'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU18'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU19'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU20'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU21'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU22'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU24'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU25'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU26'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU27'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU28'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU29'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU30'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU31'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU49'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU50'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU51'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU52'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU53'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU54'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU55'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU56'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU57'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU58'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU59'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU60'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU61'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU62'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU38'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU42'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LittleBearRiver:USU43'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'IIHR:Precipitation'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:Dissolved Oxygen'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:Dissolved Oxygen Saturation'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:Specific Conductance'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:Turbidity'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:Tempurature'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'CCDO:NO3N'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'BESSoil:SurfaceTemperature'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'BESSoil:SoilTemperature'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'BESSoil:WaterTableDepth'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Specific_conductance'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Temperature'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Temperature_hourly'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Specific_conduct_hourly'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:SurfWaterLev'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Discharge'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:GWSpecific_conductance'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:GWTemperature'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Specific_cond_daily'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Temperature_daily'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:DO_pct'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:DO_mgL'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Turbidity'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:BaroPressure'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:WaterLevelFeet'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Precip'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Water level'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'MPE:825'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'MAST_OD:Mast_V001'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'MAST_OD:Mast_V002'">Chlorophyll a</xsl:when>
                <xsl:when test="$VariableCode = 'MAST_OD:Mast_V003'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'MAST_OD:Mast_V004'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Nitrite_Nitrate'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:TP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:Nitrate'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'TWDBWind:Dir'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'TWDBWind:Speed'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'HIS:LBL9'">Water depth, stream</xsl:when>
                <xsl:when test="$VariableCode = 'HIS:LBL11'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'HIS:LBL13'">Water depth, lake</xsl:when>
                <xsl:when test="$VariableCode = 'HIS:LBL12'">Volume</xsl:when>
                <xsl:when test="$VariableCode = 'LBL:LBL8'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'LBL:LBL9'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'HIS:LBL8'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'LBL:LBL11'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LBL:LBL13'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'LBL:LBL12'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'HydroNEXRAD:843'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'BaltimorePrecip:PRECIP'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Pcp_mm'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Thravg'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:wndsphravg'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:solar15minavg'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Rhhravg'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:NetR'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Tdavg'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:streamT'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:WindDir'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:solar'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:wndspd'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:snowd'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:baro'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:SoilMoist'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:SoilTemp'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:LHFlux'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Pcp_in'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:RHdavg'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Tdmin'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Tdmax'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:Q_sporadic'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:stage_'">Water depth, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ODMDCEW2:stage_sporadic'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:TW'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:PA'">Atmospheric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:UD'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:US'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WV'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WC'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WP'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WS'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:PE'">Pheophytin</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:HT'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WT'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:TC'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:WX'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:TA'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:HL'">Gage height, lake</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:QR'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:SD'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:SW'">Snow water equivalent</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:HG'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:QC'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:PN'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:XR'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:LF'">Reservoir storage</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:IT'">Ice thickness</xsl:when>
                <xsl:when test="$VariableCode = 'RiverGages:UP'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:BR'">Bromide</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:CL'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:F'">Fluoride</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:N02'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:NO3'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:NTU'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:OP'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:S04'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:TP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:EC'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'ParadiseCr:TMP'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'LR:USU1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LR:USU2'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LR:USU3'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LR:USU4'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LR:USU5'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:FLOW'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:FLOW'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:LEVEL'">Level, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:LEVEL_FT'">Level, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:STANDPIPE_LEVEL'">Level, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:PRECIP'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:RAIN'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:AIR_TEMP'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:WATER_TEMP'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Lake_Level'">Level, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Lake_Level_IGLD'">Level, lake</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:PrecipNex'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V01'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V02'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V03'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V04'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V05'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'RIMP:RIMP_V06'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:00065'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'FLWI:00060'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'PWP:ISU1'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'PWP:ISU5'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'PWP:ISU4'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'PWP:ISU6'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'PWP:ISU3'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00929_sodium_mgl'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00095_spec_cond'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:depth_from_lsd'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00920_magnes_mgl'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00910_calcium_mgl'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00955_silica_mgl'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:elev_from_lsd'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00937_potass_mgl'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q01080_strontium'">Strontium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00445_carb_mgl'">Major, non-metals</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00440_bicarb_mgl'">Bicarbonate</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00945_sulfate_mgl'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00940_chloride_mg'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00951_fluoride_mg'">Fluoride</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q71850_nitrate_mgl'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00403_ph'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q70300_tds'">Residue, total filterable (dried at 105
                                                  C)</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00415_phen_alk'">Major, non-metals</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00410_total_alk'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00900_tot_hardnes'">Hardness, total</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00932_percent_na'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'GW_Edwards:q00931_sar'">Sodium adsorption ratio</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:TA'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:WD'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:WS'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:NEE'">Carbon dioxide flux </xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:FC'">Carbon dioxide flux </xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:SFC'">Carbon dioxide flux </xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:H'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:LE'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:SSA'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:SLE'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:G1'">Soil heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:TS'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:PRECIP'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:RH'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:PA'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:CO2'">Carbon dioxide</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:VPD'">Vapor pressure deficit</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:SWC'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:RNET'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:PAR'">Radiation, incoming PAR</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:PAR_out'">Radiation, outgoing PAR</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:Rg'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:Rg_out'">Radiation, outgoing shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:Rlong_in'">Radiation, incoming longwave</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:Rlong_out'">Radiation, outgoing longwave</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:FH2O'">Evapotranspiration, actual</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:H2O'">Water content, air</xsl:when>
                <xsl:when test="$VariableCode = 'AmeriFlux:RE'">Carbon dioxide flux </xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:HMP_Tmp_a'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Temp_Min_C'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Temp_Max_C'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:RH_Min'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:RH_Max'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Wind_Speed_Hor_Ave'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Radiation_Net_Ave'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:ET_Penman'">Evapotranspiration, potential</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:ET_JH'">Evapotranspiration, potential</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Temp_Mean_C'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:pr'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:svpma'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:svpmi'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:vpa1'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:vpdiff'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:vps1'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:wind2m'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:GWTemp'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:WaterTable'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:H_Ts'">Sensible heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Dma'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Dda'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:e'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:L_c'">Distance</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:z'">Distance</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Uavg'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:h2o_AVG'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:shf1_AVG'">Radiation, outgoing longwave</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:shf2_AVG'">Radiation, outgoing longwave</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:P_mb'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:LE'">Latent heat flux</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:HMP_e_a'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:co2_a'">Carbon dioxide</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:irga_P_kPa'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:ws_ms'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:wd'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:wd_STD'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:ws_STD'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Precip'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Tsoil'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:del_Tsoil'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:soil_water'">Water content, soil</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:P_mb_2'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:hor_wind_AVG'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:rho_a_AVG'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:wnd_dir_compass'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:wnd_dir_csat3'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:rslt_wnd_spd'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:rho_a_std'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:HMP_e_std'">Vapor pressure</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:HMP_Tmp_std'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:std_wnd_dir'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:PAR_AVG'">Radiation, incoming PAR</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Rg_AVG'">Radiation, incoming shortwave</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Ts_Avg'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:h2o_a'">Air, water vapor density</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Uy_Avg'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Ux_Avg'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Uz_Avg'">Velocity, wind</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeET:Fc'">Carbon dioxide flux </xsl:when>
                <xsl:when test="$VariableCode = 'HermineFlood:00060'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Barometricpressure2'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Streamflow1'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Relativehumidity4'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Winddirection6'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Precipitation7'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_ariz:Precipitation8'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:acid_neutralizing_capacity'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:CA_plus_plus'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Mg_plus_plus'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Na_plus'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:K_plus'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Cl_'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:NO3_'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:SO4__'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Si'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:total_N'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:dissolved_N'">Nitrogen, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:total_P'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:total_P'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:dissolved_organic_N'">Nitrogen, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:dissolved_P'">Phosphorus, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:dissolved_organic_P'">Phosphorus, dissolved organic </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:O18'">Oxygen-18</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Total_Organic_Carbon'">Carbon, total organic</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:Dissolved_Organic_Carbon'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_boulder:pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_merced:Volumetricwatercontent1'">Volume, lake</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_merced:Temperature29'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_merced:SnowDepth57'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_merced:Temperature64'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_merced:Temperature16'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Gageheight1'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:SpecificConductance3'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Sodium18'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Gageheight2'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:pH2'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Alkalinitytotal5'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Calcium10'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Magnesium14'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Chloride26'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Sulfate30'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Nitrogentotalkjeldahl41'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Phosphorustotal46'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Phosphorustotal46'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Phosphorustotaldissolved48'">Phosphorus, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Carbondissolvedorganic4'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:NitrogennitrateNO334'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:NitrogennitriteNO237'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:temperature2'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Silicon7'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Potassium22'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Discharge3'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_udel:Discharge4'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Aluminium'">Aluminum</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Ammonia_as_N'">Ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Barium'">Barium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Beryllium'">Beryllium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Boron'">Boron</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Bromide'">Bromide</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Cadmium'">Cadmium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Calcium'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Chloride'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Chromium'">Chromium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Cobalt'">Cobalt</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Conductivity'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Copper'">Copper</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Dissolved_Organic_Carbon'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:E_Coli'">Escherichia coli</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Fluoride'">Fluoride</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Hardness'">Hardness, total</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Iron'">Iron</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Lead'">Lead</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Magnesium'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Manganese'">Manganese</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Discharge_L'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:DO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:DO_Charge'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:DO_Percent'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Hardness_as_CaCO3'">Hardness, carbonate</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Nitrogen-ammonia_amonium'">Ammonium ammonia ratio</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Nitrogen-Nitrate'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Nitrogen-nitrite'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Nitrogen-nitrite_nitrate'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Phosphorous'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Potassium'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Sodium'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Solids._Dissolved'">Solids, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Solids._Suspended'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Solids._Total'">Solids, total</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:SpCond'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Sulphate'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Total_Kjeldahl_Nitrogen'">Nitrogen, total kjeldahl</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Turbidity'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Water_Temperature'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Molybdenum'">Molybdenum</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Nickel'">Nickel</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Silver'">Silver</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Strontium'">Strontium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Thallium'">Thallium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Titanium'">Titanium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Total_Coliform'">Coliform, total</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Alkalinity'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Vanadium'">Vanadium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Zinc'">Zinc</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Bismuth'">Bismuth</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Discharge_'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Fecal_Strep'">Streptococci, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Pseudomonas'">Pseudomonas</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Redox'">Oxidation reduction potential</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Saline'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Temperature'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Sulphur'">Sulfur</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Tin'">Tin</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Uranium'">Uranium</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Total_Reactive_Phosphorous'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Malathion'">Malathion</xsl:when>
                <xsl:when test="$VariableCode = 'NPCA:Methoprene'">Methoprene</xsl:when>
                <xsl:when test="$VariableCode = 'ODMRCEW2:hourly-precipitation'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'ODMRCEW2:discharge'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ODMRCEW2:supra-hourly-soil-temperature'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'ODMRCEW2:hourly-soil-temperature-inst'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'ODMPMRW2:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:PH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:SALINITY'">Salinity</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:WTEMP'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:MOIST'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:SAND'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:SILTCLAY'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TC'">Carbon, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TN'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX030-AFDW'">Ampithoe Longimannia</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX052-COUNT'">Aricidea catherinae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX051-AFDW'">Aricidea catherinae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX459-AFDW'">Pista cristata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX459-COUNT'">Pista cristata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX098-COUNT'">Capitellides jonesi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX098-AFDW'">Capitellides jonesi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX199-AFDW'">Enchytraeidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX410-COUNT'">Pagurus politus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX410-AFDW'">Pagurus politus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX182-AFDW'">Dosinia discus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX182-COUNT'">Dosinia discus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX124-COUNT'">Cirrophorus furcatus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX124-AFDW'">Cirrophorus furcatus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX599-COUNT'">Tubificidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX599-AFDW'">Tubificidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX409-COUNT'">Pagurus politus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX409-AFDW'">Pagurus politus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX485-COUNT'">Prionospio heterobranchia</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX485-AFDW'">Prionospio heterobranchia</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX055-COUNT'">Aricidea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX054-AFDW'">Aricidea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX541-COUNT'">Sphaerium</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX541-AFDW'">Sphaerium</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX097-AFDW'">Capitellides jonesi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX097-COUNT'">Capitellides jonesi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX554-COUNT'">Stenothoe minuta</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX554-AFDW'">Stenothoe minuta</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX043-COUNT'">Anomia simplex</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX042-AFDW'">Anomia simplex</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX564-COUNT'">Syllidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX117-COUNT'">Chiridotea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX564-AFDW'">Syllidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX367-COUNT'">Nassarius vibex</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX457-COUNT'">Pinnixa</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX586-COUNT'">Tharyx</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX586-AFDW'">Tharyx</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX039-COUNT'">Ancistrosyllis</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX404-COUNT'">Orbiniidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX503-COUNT'">Pseudeurythoe ambigua</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX528-COUNT'">Scoloplos</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX547-COUNT'">Spiophanes bombyx</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX038-AFDW'">Ancistrosyllis</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX404-AFDW'">Orbiniidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX503-AFDW'">Pseudeurythoe ambigua</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX528-AFDW'">Scoloplos</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX547-AFDW'">Spiophanes bombyx</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX526-COUNT'">Scolelepis texana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX526-AFDW'">Scolelepis texana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX408-COUNT'">Oxyurostylis smithi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX408-AFDW'">Oxyurostylis smithi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX050-COUNT'">Arabellidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX049-AFDW'">Arabellidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX323-COUNT'">Marphysa</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX323-AFDW'">Marphysa</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX212-COUNT'">Eteone lactea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX212-AFDW'">Eteone lactea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX484-COUNT'">Potamothrix vejdovsky</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX484-AFDW'">Potamothrix vejdovsky</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX202-COUNT'">Ephemeroptera</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX202-AFDW'">Ephemeroptera</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX307-COUNT'">Lumbrineridae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX307-AFDW'">Lumbrineridae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX042-COUNT'">Ancylidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX058-COUNT'">Asellus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX041-AFDW'">Ancylidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX058-AFDW'">Asellus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX529-COUNT'">Seila adamsi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX529-AFDW'">Seila adamsi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX463-COUNT'">Pleurocera</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX463-AFDW'">Pleurocera</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX276-COUNT'">Kurtziella</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX276-AFDW'">Kurtziella</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX302-AFDW'">Listriella</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX302-COUNT'">Listriella</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX352-COUNT'">Mytilidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:CONDUCT'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:DO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX123-COUNT'">Cirratulidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX025-COUNT'">Ampelisca</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX023-COUNT'">Ampelisca</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX136-COUNT'">Coenagrionidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX475-COUNT'">Polypedilum</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX147-COUNT'">Cricotopus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX147-AFDW'">Cricotopus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX237-AFDW'">Glyptotendipes</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX481-AFDW'">Polypedilum digitifer</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX572-AFDW'">Tanaidacea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX390-COUNT'">Odonata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX390-AFDW'">Odonata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX310-COUNT'">Lysidice ninetta</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX310-AFDW'">Lysidice ninetta</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX033-COUNT'">Anachis avara</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX032-AFDW'">Anachis avara</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX203-COUNT'">Epitonium</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX203-AFDW'">Epitonium</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX456-COUNT'">Pinnixa sayana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX456-AFDW'">Pinnixa sayana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX305-COUNT'">Loimia</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX305-AFDW'">Loimia</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX056-COUNT'">Aricidea wassi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX055-AFDW'">Aricidea wassi</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX399-COUNT'">Onuphis eremita</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX525-COUNT'">Scolelepis squamata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX399-AFDW'">Onuphis eremita</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX525-AFDW'">Scolelepis squamata</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX052-AFDW'">Aricidea</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX472-COUNT'">Polymesoda caroliniana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX472-AFDW'">Polymesoda caroliniana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX472-AFDW'">Polymesoda caroliniana</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX227-COUNT'">Gammarus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX227-AFDW'">Gammarus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX467-COUNT'">Polinices duplicatus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX467-AFDW'">Polinices duplicatus</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX440-COUNT'">Periploma</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX440-AFDW'">Periploma</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX120-COUNT'">Chironomidae</xsl:when>
                <xsl:when test="$VariableCode = 'Benthic:TX031-COUNT'">Ampithoe Longimannia</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_catalina:Precipitation1'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_catalina:Barometricpressure2'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_catalina:Temperature3'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'CZO_catalina:Relativehumidity4'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'NLDAS:NLDAS_MOS0125_H.002:soilm0_10cm'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'NLDAS:NLDAS_MOS0125_H.002:tsoildeep'">Temperature, soil</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TEMP'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_SPCOND'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_DO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_DOSAT'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_CHL'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_ALK'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_ACID'">Acidity</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_BOD'">Biochemical oxygen demand</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_COD'">Chemical oxygen demand</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TOC'">Carbon, total organic</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TSS'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TDS'">Solids, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_FC'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_EC'">Escherichia coli</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_ENT'">Enterococci</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TN'">Nitrogen, total </xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_NH4'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_NO2'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_NO3'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TP'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_PO4'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_COLOR'">Color</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TURB'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_ZN'">Zinc</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_CR'">Chromium</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_PB'">Lead</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_CU'">Copper</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_AS'">Arsenic</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_OG'">Oil and grease  CWA 304B</xsl:when>
                <xsl:when test="$VariableCode = 'MR:MuddyRiver_TPH'">Hydrocarbons, petroleum</xsl:when>
                <xsl:when test="$VariableCode = 'CZSNW:8'">Snow depth</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:IC_GW'">Carbon, dissolved inorganic</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NH4_GW'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NO2_GW'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NO3_GW'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:OC_GW'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:pH_GW'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:RP_GW'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:T_GW'">Temperature, 1 meter below water surface</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TC_GW'">Carbon, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TP_GW'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TSS_GW'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:Turbidity_GW'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:WL_GW'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:N-15_GW'">Nitrogen-15</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:O-18_GW'">Oxygen-18</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:Cond_SW'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:IC_SW'">Carbon, dissolved inorganic</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NH4_SW'">Ammonium</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NO2_SW'">Nitrogen, nitrite (NO2) </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:NO3_SW'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:OC_SW'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:pH_SW'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:RP_SW'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:T_SW'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TC_SW'">Carbon, total dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TP_SW'">Phosphorus, total </xsl:when>
                <xsl:when test="$VariableCode = 'GRP:TSS_SW'">Solids, total suspended</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:Turbidity_SW'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:WL_SW'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'GRP:Cond_GW'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'NWS-WGRFC:MPE'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWS-WGRFC:MPE'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWS-WGRFC:MPE'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'NWS-WGRFC:MPE'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeETWells:GWTemp'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'RioGrandeETWells:WaterTable'">Groundwater level</xsl:when>
                <xsl:when test="$VariableCode = 'COWEETA:Precip'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'COWEETA:Airtemp_Mean'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'COWEETA:Airtemp_Absmin'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'COWEETA:Airtemp_Absmax'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'COWEETA:Discharge'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'ODM:COSMOS03'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'ODM:COSMOS01'">Soil Moisture</xsl:when>
                <xsl:when test="$VariableCode = 'HCLIMATE:TMIN'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'HCLIMATE:TAVG'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'HCLIMATE:TMAX'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'HCLIMATE:PRCP'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:AL'">Aluminum</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:ALK'">Alkalinity</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:Ca'">Calcium</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:Cl'">Chloride</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:Color'">Color</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:FE'">Iron, ferrous</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:K'">Potassium</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:MG'">Magnesium</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:MN'">Manganese</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:NA'">Sodium</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:NO3_N'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:pH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:SI'">Silica</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:SO4'">Sulfate</xsl:when>
                <xsl:when test="$VariableCode = 'MAWRRC:CU'">Copper</xsl:when>
                <xsl:when test="$VariableCode = 'ODMSRB:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'MOSS:IDCS-1-Avg'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'MOSS:IDCS-10-Avg'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'MOSS:IDCS-2-Avg'">Coliform, fecal</xsl:when>
                <xsl:when test="$VariableCode = 'MOSS:IDCS-3-Avg'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:WT'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:AT'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:BP'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:DP'">Dew point temperature </xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:RF5'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:RFH'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'DEOS:RH'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:PH'">pH</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:PRES'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:ORP'">Oxidation reduction potential</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:56'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:610'">Ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:630'">Nitrogen, nitrate (NO3) </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:DEPTH'">Water depth, stream</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:DO'">Oxygen, dissolved</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:DOC-SW'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:DoSat'">Oxygen, dissolved percent of
                                                  saturation</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:Fgt2m'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:SPCOND'">Specific conductance</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:SSFdw'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:SSFloi'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:SSMdw'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:SSMloi'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:Temp'">Temperature, water</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TN-AD'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TN-DW'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TN-IG'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TN-SW'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TN-SWNR'">Nitrogen, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNH4-AD'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNH4-DW'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNH4-IG'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNH4-SW'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNH4-SWNR'">Total ammonia</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNO2-3-AD'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNO2-3-DW'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNO2-3-IG'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNO2-3-SW'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TNO2-SW'">Nitrogen, nitrite (NO2) + nitrate
                                                  (NO3)</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TOC-IG'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TOC-SW'">Carbon, dissolved organic</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TP-AD'">Phosphorus, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TP-DW'">Phosphorus, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TP-IG'">Phosphorus, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TP-SW'">Phosphorus, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TP-SWNR'">Phosphorus, total organic </xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TRP-AD'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TRP-DW'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TRP-IG'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TRP-SW'">Phosphorus, orthophosphate</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TsedW1'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TsedW2'">Suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TURB'">Turbidity</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TUREA-AD'">Urea, phenyl-</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TUREA-DW'">Urea, phenyl-</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TUREA-IG'">Urea, phenyl-</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TUREA-SW'">Urea, phenyl-</xsl:when>
                <xsl:when test="$VariableCode = 'EFW:TUREA-SWNR'">Urea, phenyl-</xsl:when>
                <xsl:when test="$VariableCode = 'LaSelva:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LaSelva:Qgap'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LaSelva:Qman'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LaSelva:S'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'LaSelva:Sman'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'TM:A'">Surface area, suspended sediment</xsl:when>
                <xsl:when test="$VariableCode = 'TM:H_m'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'TM:Q'">Discharge, stream</xsl:when>
                <xsl:when test="$VariableCode = 'TM:V'">Velocity, stream</xsl:when>
                <xsl:when test="$VariableCode = 'TM:H_ft'">Gage height, stream</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Rad'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Temp'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Wdir'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Wsp'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Gdir'">Wind gust direction</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Gsp'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Hum'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Prec'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'HB:Pres'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Hum'">Relative humidity</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Pres'">Barometric pressure</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Rad'">Radiation, net</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Temp'">Temperature, air</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Wsp'">Sustained wind speed</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Gdir'">Wind gust direction</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Gsp'">Wind gust</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Prec'">Precipitation</xsl:when>
                <xsl:when test="$VariableCode = 'WB:Wdir'">Wind direction</xsl:when>
                <xsl:when test="$VariableCode = 'ABRFC:MPE'">Precipitation</xsl:when>
            </xsl:choose>
            </xsl:template>
 -->
        </xsl:stylesheet>
        
    
