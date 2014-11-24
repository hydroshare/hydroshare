<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:hisc="http://hiscentral.cuahsi.org/20100205/" 
    version="1.0">
    <xsl:template name="HisUOMMapper">
        <xsl:param name="UnitString"/>
      
        <xsl:variable name="mappedUnit" select="document('../HisControlledVocabularies/UnitsCv_2011_10_04.xml')//hisc:Record/hisc:UnitsName[text()=$UnitString]/../hisc:UnitsAbbreviation"/> 
   <xsl:choose>
      <xsl:when  test="$mappedUnit">
       <xsl:value-of select="$mappedUnit"/>
      </xsl:when>
   <xsl:otherwise>
       <xsl:value-of select="UnitString"/>
   </xsl:otherwise>
   </xsl:choose>
       

    </xsl:template>  
        <!--    <xsl:template name="HisUOMMapper">
        <xsl:param name="UnitString"/>
       <xsl:choose>
           <xsl:when test="$UnitString = 'percent'">%</xsl:when>
            <xsl:when test="$UnitString = '%'">%</xsl:when>
            <xsl:when test="$UnitString = 'degree'">deg</xsl:when>
            <xsl:when test="$UnitString = 'deg'">deg</xsl:when>
            <xsl:when test="$UnitString = 'grad'">grad</xsl:when>
            <xsl:when test="$UnitString = 'grad'">grad</xsl:when>
            <xsl:when test="$UnitString = 'radian'">rad</xsl:when>
            <xsl:when test="$UnitString = 'rad'">rad</xsl:when>
            <xsl:when test="$UnitString = 'degree north'">degN</xsl:when>
            <xsl:when test="$UnitString = 'degN'">degN</xsl:when>
            <xsl:when test="$UnitString = 'degree south'">degS</xsl:when>
            <xsl:when test="$UnitString = 'degS'">degS</xsl:when>
            <xsl:when test="$UnitString = 'degree west'">degW</xsl:when>
            <xsl:when test="$UnitString = 'degW'">degW</xsl:when>
            <xsl:when test="$UnitString = 'degree east'">degE</xsl:when>
            <xsl:when test="$UnitString = 'degE'">degE</xsl:when>
            <xsl:when test="$UnitString = 'arcminute'">arcmin</xsl:when>
            <xsl:when test="$UnitString = 'arcmin'">arcmin</xsl:when>
            <xsl:when test="$UnitString = 'arcsecond'">arcsec</xsl:when>
            <xsl:when test="$UnitString = 'arcsec'">arcsec</xsl:when>
            <xsl:when test="$UnitString = 'steradian'">sr</xsl:when>
             <xsl:when test="$UnitString = 'sr'">sr</xsl:when>
            <xsl:when test="$UnitString = 'acre'">ac</xsl:when>
            <xsl:when test="$UnitString = 'ac'">ac</xsl:when>
            <xsl:when test="$UnitString = 'hectare'">ha</xsl:when>
            <xsl:when test="$UnitString = 'ha'">ha</xsl:when>
            <xsl:when test="$UnitString = 'square centimeter'">cm^2</xsl:when>
            <xsl:when test="$UnitString = 'cm^2'">cm^2</xsl:when>
            <xsl:when test="$UnitString = 'square foot'">ft^2</xsl:when>
            <xsl:when test="$UnitString = 'ft^2'">ft^2</xsl:when>
            <xsl:when test="$UnitString = 'square kilometer'">km^2</xsl:when>
            <xsl:when test="$UnitString = 'km^2'">km^2</xsl:when>
            <xsl:when test="$UnitString = 'square meter'">m^2</xsl:when>
            <xsl:when test="$UnitString = 'm^2'">m^2</xsl:when>
            <xsl:when test="$UnitString = 'square mile'">mi^2</xsl:when>
            <xsl:when test="$UnitString = 'mi^2'">mi^2</xsl:when>
            <xsl:when test="$UnitString = 'hertz'">Hz</xsl:when>
            <xsl:when test="$UnitString = 'Hz'">Hz</xsl:when>
            <xsl:when test="$UnitString = 'darcy'">D</xsl:when>
            <xsl:when test="$UnitString = 'D'">D</xsl:when>
            <xsl:when test="$UnitString = 'british thermal unit'">BTU</xsl:when>
            <xsl:when test="$UnitString = 'BTU'">BTU</xsl:when>
            <xsl:when test="$UnitString = 'calorie'">cal</xsl:when>
            <xsl:when test="$UnitString = 'cal'">cal</xsl:when>
            <xsl:when test="$UnitString = 'erg'">erg</xsl:when>
            <xsl:when test="$UnitString = 'erg'">erg</xsl:when>
            <xsl:when test="$UnitString = 'foot pound force'">lbf ft</xsl:when>
            <xsl:when test="$UnitString = 'lbf ft'">lbf ft</xsl:when>
            <xsl:when test="$UnitString = 'joule'">J</xsl:when>
            <xsl:when test="$UnitString = 'J'">J</xsl:when>
            <xsl:when test="$UnitString = 'kilowatt hour'">kW hr</xsl:when>
            <xsl:when test="$UnitString = 'kW hr'">kW hr</xsl:when>
            <xsl:when test="$UnitString = 'electronvolt'">eV</xsl:when>
            <xsl:when test="$UnitString = 'eV'">eV</xsl:when>
            <xsl:when test="$UnitString = 'langleys per day'">Ly/d</xsl:when>
            <xsl:when test="$UnitString = 'Ly/d'">Ly/d</xsl:when>
            <xsl:when test="$UnitString = 'langleys per minute'">Ly/min</xsl:when>
            <xsl:when test="$UnitString = 'Ly/min'">Ly/min</xsl:when>
            <xsl:when test="$UnitString = 'langleys per second'">Ly/s</xsl:when>
            <xsl:when test="$UnitString = 'Ly/s'">Ly/s</xsl:when>
            <xsl:when test="$UnitString = 'megajoules per square meter per day'">MJ/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'MJ/m^2 d'">MJ/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'watts per square centimeter'">W/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'W/cm^2'">W/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'watts per square meter'">W/m^2</xsl:when>
            <xsl:when test="$UnitString = 'W/m^2'">W/m^2</xsl:when>
            <xsl:when test="$UnitString = 'acre feet per year'">ac ft/yr</xsl:when>
            <xsl:when test="$UnitString = 'ac ft/yr'">ac ft/yr</xsl:when>
            <xsl:when test="$UnitString = 'cubic feet per second'">cfs</xsl:when>
            <xsl:when test="$UnitString = 'cfs'">cfs</xsl:when>
            <xsl:when test="$UnitString = 'cubic meters per second'">m^3/s</xsl:when>
            <xsl:when test="$UnitString = 'm^3/s'">m^3/s</xsl:when>
            <xsl:when test="$UnitString = 'cubic meters per day'">m^3/d</xsl:when>
            <xsl:when test="$UnitString = 'm^3/d'">m^3/d</xsl:when>
            <xsl:when test="$UnitString = 'gallons per minute'">gpm</xsl:when>
            <xsl:when test="$UnitString = 'gpm'">gpm</xsl:when>
            <xsl:when test="$UnitString = 'liters per second'">L/s</xsl:when>
            <xsl:when test="$UnitString = 'L/s'">L/s</xsl:when>
            <xsl:when test="$UnitString = 'million gallons per day'">MGD</xsl:when>
            <xsl:when test="$UnitString = 'MGD'">MGD</xsl:when>
            <xsl:when test="$UnitString = 'dyne'">dyn</xsl:when>
            <xsl:when test="$UnitString = 'dyn'">dyn</xsl:when>
            <xsl:when test="$UnitString = 'kilogram force'">kgf</xsl:when>
            <xsl:when test="$UnitString = 'kgf'">kgf</xsl:when>
            <xsl:when test="$UnitString = 'newton'">N</xsl:when>
            <xsl:when test="$UnitString = 'N'">N</xsl:when>
            <xsl:when test="$UnitString = 'pound force'">lbf</xsl:when>
            <xsl:when test="$UnitString = 'lbf'">lbf</xsl:when>
            <xsl:when test="$UnitString = 'kilo pound force'">kip</xsl:when>
            <xsl:when test="$UnitString = 'kip'">kip</xsl:when>
            <xsl:when test="$UnitString = 'ounce force'">ozf</xsl:when>
            <xsl:when test="$UnitString = 'ozf'">ozf</xsl:when>
            <xsl:when test="$UnitString = 'centimeter '">cm</xsl:when>
            <xsl:when test="$UnitString = 'cm'">cm</xsl:when>
            <xsl:when test="$UnitString = 'international foot'">ft</xsl:when>
            <xsl:when test="$UnitString = 'ft'">ft</xsl:when>
            <xsl:when test="$UnitString = 'international inch'">in</xsl:when>
            <xsl:when test="$UnitString = 'in'">in</xsl:when>
            <xsl:when test="$UnitString = 'international yard'">yd</xsl:when>
            <xsl:when test="$UnitString = 'yd'">yd</xsl:when>
            <xsl:when test="$UnitString = 'kilometer'">km</xsl:when>
            <xsl:when test="$UnitString = 'km'">km</xsl:when>
            <xsl:when test="$UnitString = 'meter'">m</xsl:when>
            <xsl:when test="$UnitString = 'm'">m</xsl:when>
            <xsl:when test="$UnitString = 'international mile'">mi</xsl:when>
            <xsl:when test="$UnitString = 'mi'">mi</xsl:when>
            <xsl:when test="$UnitString = 'millimeter'">mm</xsl:when>
            <xsl:when test="$UnitString = 'mm'">mm</xsl:when>
            <xsl:when test="$UnitString = 'micron'">um</xsl:when>
            <xsl:when test="$UnitString = 'um'">um</xsl:when>
            <xsl:when test="$UnitString = 'angstrom'">Å</xsl:when>
            <xsl:when test="$UnitString = 'Å'">Å</xsl:when>
            <xsl:when test="$UnitString = 'femtometer'">fm</xsl:when>
            <xsl:when test="$UnitString = 'fm'">fm</xsl:when>
            <xsl:when test="$UnitString = 'nautical mile'">nmi</xsl:when>
            <xsl:when test="$UnitString = 'nmi'">nmi</xsl:when>
            <xsl:when test="$UnitString = 'lumen'">lm</xsl:when>
            <xsl:when test="$UnitString = 'lm'">lm</xsl:when>
            <xsl:when test="$UnitString = 'lux'">lx</xsl:when>
            <xsl:when test="$UnitString = 'lx'">lx</xsl:when>
            <xsl:when test="$UnitString = 'lambert'">La</xsl:when>
            <xsl:when test="$UnitString = 'La'">La</xsl:when>
            <xsl:when test="$UnitString = 'stilb'">sb</xsl:when>
            <xsl:when test="$UnitString = 'sb'">sb</xsl:when>
            <xsl:when test="$UnitString = 'phot'">ph</xsl:when>
            <xsl:when test="$UnitString = 'ph'">ph</xsl:when>
            <xsl:when test="$UnitString = 'langley'">Ly</xsl:when>
            <xsl:when test="$UnitString = 'Ly'">Ly</xsl:when>
            <xsl:when test="$UnitString = 'gram'">g</xsl:when>
            <xsl:when test="$UnitString = 'g'">g</xsl:when>
            <xsl:when test="$UnitString = 'kilogram'">kg</xsl:when>
            <xsl:when test="$UnitString = 'kg'">kg</xsl:when>
            <xsl:when test="$UnitString = 'milligram'">mg</xsl:when>
            <xsl:when test="$UnitString = 'mg'">mg</xsl:when>
            <xsl:when test="$UnitString = 'microgram'">ug</xsl:when>
            <xsl:when test="$UnitString = 'ug'">ug</xsl:when>
            <xsl:when test="$UnitString = 'pound mass (avoirdupois)'">lb</xsl:when>
            <xsl:when test="$UnitString = 'lb'">lb</xsl:when>
            <xsl:when test="$UnitString = 'slug'">slug</xsl:when>
            <xsl:when test="$UnitString = 'slug'">slug</xsl:when>
            <xsl:when test="$UnitString = 'metric ton'">tonne</xsl:when>
            <xsl:when test="$UnitString = 'tonne'">tonne</xsl:when>
            <xsl:when test="$UnitString = 'grain'">grain</xsl:when>
            <xsl:when test="$UnitString = 'grain'">grain</xsl:when>
            <xsl:when test="$UnitString = 'carat'">car</xsl:when>
            <xsl:when test="$UnitString = 'car'">car</xsl:when>
            <xsl:when test="$UnitString = 'atomic mass unit'">amu</xsl:when>
            <xsl:when test="$UnitString = 'amu'">amu</xsl:when>
            <xsl:when test="$UnitString = 'short ton'">ton</xsl:when>
            <xsl:when test="$UnitString = 'ton'">ton</xsl:when>
            <xsl:when test="$UnitString = 'BTU per hour'">BTU/hr</xsl:when>
            <xsl:when test="$UnitString = 'BTU/hr'">BTU/hr</xsl:when>
            <xsl:when test="$UnitString = 'foot pound force per second'">lbf/s</xsl:when>
            <xsl:when test="$UnitString = 'lbf/s'">lbf/s</xsl:when>
            <xsl:when test="$UnitString = 'horse power (shaft)'">hp</xsl:when>
            <xsl:when test="$UnitString = 'hp'">hp</xsl:when>
            <xsl:when test="$UnitString = 'kilowatt'">kW</xsl:when>
            <xsl:when test="$UnitString = 'kW'">kW</xsl:when>
            <xsl:when test="$UnitString = 'watt'">W</xsl:when>
            <xsl:when test="$UnitString = 'W'">W</xsl:when>
            <xsl:when test="$UnitString = 'voltampere'">VA</xsl:when>
            <xsl:when test="$UnitString = 'VA'">VA</xsl:when>
            <xsl:when test="$UnitString = 'atmospheres'">atm</xsl:when>
            <xsl:when test="$UnitString = 'atm'">atm</xsl:when>
            <xsl:when test="$UnitString = 'pascal'">Pa</xsl:when>
            <xsl:when test="$UnitString = 'Pa'">Pa</xsl:when>
            <xsl:when test="$UnitString = 'inch of mercury'">inch Hg</xsl:when>
            <xsl:when test="$UnitString = 'inch Hg'">inch Hg</xsl:when>
            <xsl:when test="$UnitString = 'inch of water'">inch H2O</xsl:when>
            <xsl:when test="$UnitString = 'inch H2O'">inch H2O</xsl:when>
            <xsl:when test="$UnitString = 'millimeter of mercury'">mm Hg</xsl:when>
            <xsl:when test="$UnitString = 'mm Hg'">mm Hg</xsl:when>
            <xsl:when test="$UnitString = 'millimeter of water'">mm H2O</xsl:when>
            <xsl:when test="$UnitString = 'mm H2O'">mm H2O</xsl:when>
            <xsl:when test="$UnitString = 'centimeter of mercury'">cm Hg</xsl:when>
            <xsl:when test="$UnitString = 'cm Hg'">cm Hg</xsl:when>
            <xsl:when test="$UnitString = 'centimeter of water'">cm H2O</xsl:when>
            <xsl:when test="$UnitString = 'cm H2O'">cm H2O</xsl:when>
            <xsl:when test="$UnitString = 'millibar'">mbar</xsl:when>
            <xsl:when test="$UnitString = 'mbar'">mbar</xsl:when>
            <xsl:when test="$UnitString = 'pound force per square inch'">psi</xsl:when>
            <xsl:when test="$UnitString = 'psi'">psi</xsl:when>
            <xsl:when test="$UnitString = 'torr'">torr</xsl:when>
            <xsl:when test="$UnitString = 'torr'">torr</xsl:when>
            <xsl:when test="$UnitString = 'barie'">barie</xsl:when>
            <xsl:when test="$UnitString = 'barie'">barie</xsl:when>
            <xsl:when test="$UnitString = 'meters per pixel'">meters per pixel</xsl:when>
            <xsl:when test="$UnitString = 'meters per pixel'">meters per pixel</xsl:when>
            <xsl:when test="$UnitString = 'meters per meter'">-</xsl:when>
            <xsl:when test="$UnitString = '-'">-</xsl:when>
            <xsl:when test="$UnitString = 'degree celsius'">degC</xsl:when>
            <xsl:when test="$UnitString = 'degC'">degC</xsl:when>
            <xsl:when test="$UnitString = 'degree fahrenheit'">degF</xsl:when>
            <xsl:when test="$UnitString = 'degF'">degF</xsl:when>
            <xsl:when test="$UnitString = 'degree rankine'">degR</xsl:when>
            <xsl:when test="$UnitString = 'degR'">degR</xsl:when>
            <xsl:when test="$UnitString = 'degree kelvin'">degK</xsl:when>
            <xsl:when test="$UnitString = 'degK'">degK</xsl:when>
            <xsl:when test="$UnitString = 'second'">s</xsl:when>
            <xsl:when test="$UnitString = 's'">s</xsl:when>
            <xsl:when test="$UnitString = 'millisecond'">millisec</xsl:when>
            <xsl:when test="$UnitString = 'millisec'">millisec</xsl:when>
            <xsl:when test="$UnitString = 'minute'">min</xsl:when>
            <xsl:when test="$UnitString = 'min'">min</xsl:when>
            <xsl:when test="$UnitString = 'hour'">hr</xsl:when>
            <xsl:when test="$UnitString = 'hr'">hr</xsl:when>
            <xsl:when test="$UnitString = 'day'">d</xsl:when>
            <xsl:when test="$UnitString = 'd'">d</xsl:when>
            <xsl:when test="$UnitString = 'week'">week</xsl:when>
            <xsl:when test="$UnitString = 'week'">week</xsl:when>
            <xsl:when test="$UnitString = 'month'">month</xsl:when>
            <xsl:when test="$UnitString = 'month'">month</xsl:when>
            <xsl:when test="$UnitString = 'common year (365 days)'">yr</xsl:when>
            <xsl:when test="$UnitString = 'yr'">yr</xsl:when>
            <xsl:when test="$UnitString = 'leap year (366 days)'">leap yr</xsl:when>
            <xsl:when test="$UnitString = 'leap yr'">leap yr</xsl:when>
            <xsl:when test="$UnitString = 'Julian year (365.25 days)'">jul yr</xsl:when>
            <xsl:when test="$UnitString = 'jul yr'">jul yr</xsl:when>
            <xsl:when test="$UnitString = 'Gregorian year (365.2425 days)'">greg yr</xsl:when>
            <xsl:when test="$UnitString = 'greg yr'">greg yr</xsl:when>
            <xsl:when test="$UnitString = 'centimeters per hour'">cm/hr</xsl:when>
            <xsl:when test="$UnitString = 'cm/hr'">cm/hr</xsl:when>
            <xsl:when test="$UnitString = 'centimeters per second'">cm/s</xsl:when>
            <xsl:when test="$UnitString = 'cm/s'">cm/s</xsl:when>
            <xsl:when test="$UnitString = 'feet per second'">ft/s</xsl:when>
            <xsl:when test="$UnitString = 'ft/s'">ft/s</xsl:when>
            <xsl:when test="$UnitString = 'gallons per day per square foot'">gpd/ft^2</xsl:when>
            <xsl:when test="$UnitString = 'gpd/ft^2'">gpd/ft^2</xsl:when>
            <xsl:when test="$UnitString = 'inches per hour'">in/hr</xsl:when>
            <xsl:when test="$UnitString = 'in/hr'">in/hr</xsl:when>
            <xsl:when test="$UnitString = 'kilometers per hour'">km/h</xsl:when>
            <xsl:when test="$UnitString = 'km/h'">km/h</xsl:when>
            <xsl:when test="$UnitString = 'meters per day'">m/d</xsl:when>
            <xsl:when test="$UnitString = 'm/d'">m/d</xsl:when>
            <xsl:when test="$UnitString = 'meters per hour'">m/hr</xsl:when>
            <xsl:when test="$UnitString = 'm/hr'">m/hr</xsl:when>
            <xsl:when test="$UnitString = 'meters per second'">m/s</xsl:when>
            <xsl:when test="$UnitString = 'm/s'">m/s</xsl:when>
            <xsl:when test="$UnitString = 'miles per hour'">mph</xsl:when>
            <xsl:when test="$UnitString = 'mph'">mph</xsl:when>
            <xsl:when test="$UnitString = 'millimeters per hour'">mm/hr</xsl:when>
            <xsl:when test="$UnitString = 'mm/hr'">mm/hr</xsl:when>
            <xsl:when test="$UnitString = 'nautical mile per hour'">knot</xsl:when>
            <xsl:when test="$UnitString = 'knot'">knot</xsl:when>
            <xsl:when test="$UnitString = 'acre foot'">ac ft</xsl:when>
            <xsl:when test="$UnitString = 'ac ft'">ac ft</xsl:when>
            <xsl:when test="$UnitString = 'cubic centimeter'">cc</xsl:when>
            <xsl:when test="$UnitString = 'cc'">cc</xsl:when>
            <xsl:when test="$UnitString = 'cubic foot'">ft^3</xsl:when>
            <xsl:when test="$UnitString = 'ft^3'">ft^3</xsl:when>
            <xsl:when test="$UnitString = 'cubic meter'">m^3</xsl:when>
            <xsl:when test="$UnitString = 'm^3'">m^3</xsl:when>
            <xsl:when test="$UnitString = 'hectare meter'">hec m</xsl:when>
            <xsl:when test="$UnitString = 'hec m'">hec m</xsl:when>
            <xsl:when test="$UnitString = 'liter'">L</xsl:when>
            <xsl:when test="$UnitString = 'L'">L</xsl:when>
            <xsl:when test="$UnitString = 'US gallon'">gal</xsl:when>
            <xsl:when test="$UnitString = 'gal'">gal</xsl:when>
            <xsl:when test="$UnitString = 'barrel'">bbl</xsl:when>
            <xsl:when test="$UnitString = 'bbl'">bbl</xsl:when>
            <xsl:when test="$UnitString = 'pint'">pt</xsl:when>
            <xsl:when test="$UnitString = 'pt'">pt</xsl:when>
            <xsl:when test="$UnitString = 'bushel'">bu</xsl:when>
            <xsl:when test="$UnitString = 'bu'">bu</xsl:when>
            <xsl:when test="$UnitString = 'teaspoon'">tsp</xsl:when>
            <xsl:when test="$UnitString = 'tsp'">tsp</xsl:when>
            <xsl:when test="$UnitString = 'tablespoon'">tbsp</xsl:when>
            <xsl:when test="$UnitString = 'tbsp'">tbsp</xsl:when>
            <xsl:when test="$UnitString = 'quart'">qrt</xsl:when>
            <xsl:when test="$UnitString = 'qrt'">qrt</xsl:when>
            <xsl:when test="$UnitString = 'ounce'">oz</xsl:when>
            <xsl:when test="$UnitString = 'oz'">oz</xsl:when>
            <xsl:when test="$UnitString = 'dimensionless'">-</xsl:when>
            <xsl:when test="$UnitString = '-'">-</xsl:when>
            <xsl:when test="$UnitString = 'mega joule'">MJ</xsl:when>
            <xsl:when test="$UnitString = 'MJ'">MJ</xsl:when>
            <xsl:when test="$UnitString = 'degrees minutes seconds'">dddmmss</xsl:when>
            <xsl:when test="$UnitString = 'dddmmss'">dddmmss</xsl:when>
            <xsl:when test="$UnitString = 'calories per square centimeter per day'">cal/cm^2
                d</xsl:when>
            <xsl:when test="$UnitString = 'cal/cm^2 d'">cal/cm^2 d</xsl:when>
            <xsl:when test="$UnitString = 'calories per square centimeter per minute'">cal/cm^2
                min</xsl:when>
            <xsl:when test="$UnitString = 'cal/cm^2 min'">cal/cm^2 min</xsl:when>
            <xsl:when test="$UnitString = 'milliliters per square centimeter per day'">ml/cm^2
                d</xsl:when>
            <xsl:when test="$UnitString = 'ml/cm^2 d'">ml/cm^2 d</xsl:when>
            <xsl:when test="$UnitString = 'micromoles per square meter per second'">umol/m^2
                s</xsl:when>
            <xsl:when test="$UnitString = 'umol/m^2 s'">umol/m^2 s</xsl:when>
            <xsl:when test="$UnitString = 'megajoules per square meter'">MJ/m^2</xsl:when>
            <xsl:when test="$UnitString = 'MJ/m^2'">MJ/m^2</xsl:when>
            <xsl:when test="$UnitString = 'gallons per day'">gpd</xsl:when>
            <xsl:when test="$UnitString = 'gpd'">gpd</xsl:when>
            <xsl:when test="$UnitString = 'million gallons per month'">MGM</xsl:when>
            <xsl:when test="$UnitString = 'MGM'">MGM</xsl:when>
            <xsl:when test="$UnitString = 'million gallons per year'">MGY</xsl:when>
            <xsl:when test="$UnitString = 'MGY'">MGY</xsl:when>
            <xsl:when test="$UnitString = 'short tons per day per foot'">ton/d ft</xsl:when>
            <xsl:when test="$UnitString = 'ton/d ft'">ton/d ft</xsl:when>
            <xsl:when test="$UnitString = 'lumens per square foot'">lm/ft^2</xsl:when>
            <xsl:when test="$UnitString = 'lm/ft^2'">lm/ft^2</xsl:when>
            <xsl:when test="$UnitString = 'microeinsteins per square meter per second'">uE/m^2
                s</xsl:when>
            <xsl:when test="$UnitString = 'uE/m^2 s'">uE/m^2 s</xsl:when>
            <xsl:when test="$UnitString = 'alphas per meter'">a/m</xsl:when>
            <xsl:when test="$UnitString = 'a/m'">a/m</xsl:when>
            <xsl:when test="$UnitString = 'microeinsteins per square meter'">uE/m^2</xsl:when>
            <xsl:when test="$UnitString = 'uE/m^2'">uE/m^2</xsl:when>
            <xsl:when test="$UnitString = 'millimoles of photons per square meter'"
                >mmol/m^2</xsl:when>
            <xsl:when test="$UnitString = 'mmol/m^2'">mmol/m^2</xsl:when>
            <xsl:when test="$UnitString = 'absorbance per centimeter'">A/cm</xsl:when>
            <xsl:when test="$UnitString = 'A/cm'">A/cm</xsl:when>
            <xsl:when test="$UnitString = 'nanogram'">ng</xsl:when>
            <xsl:when test="$UnitString = 'ng'">ng</xsl:when>
            <xsl:when test="$UnitString = 'picogram'">pg</xsl:when>
            <xsl:when test="$UnitString = 'pg'">pg</xsl:when>
            <xsl:when test="$UnitString = 'milliequivalents'">meq</xsl:when>
            <xsl:when test="$UnitString = 'meq'">meq</xsl:when>
            <xsl:when test="$UnitString = 'grams per square meter'">g/m^2</xsl:when>
            <xsl:when test="$UnitString = 'g/m^2'">g/m^2</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per square meter'">mg/m^2</xsl:when>
            <xsl:when test="$UnitString = 'mg/m^2'">mg/m^2</xsl:when>
            <xsl:when test="$UnitString = 'micrograms per square meter'">ug/m^2</xsl:when>
            <xsl:when test="$UnitString = 'ug/m^2'">ug/m^2</xsl:when>
            <xsl:when test="$UnitString = 'grams per square meter per day'">g/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'g/m^2 d'">g/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'grams per day'">g/d</xsl:when>
            <xsl:when test="$UnitString = 'g/d'">g/d</xsl:when>
            <xsl:when test="$UnitString = 'pounds per day'">lb/d</xsl:when>
            <xsl:when test="$UnitString = 'lb/d'">lb/d</xsl:when>
            <xsl:when test="$UnitString = 'pounds per mile'">lb/mi</xsl:when>
            <xsl:when test="$UnitString = 'lb/mi'">lb/mi</xsl:when>
            <xsl:when test="$UnitString = 'short tons per day'">ton/d</xsl:when>
            <xsl:when test="$UnitString = 'ton/d'">ton/d</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per cubic meter per day'">mg/m^3 d</xsl:when>
            <xsl:when test="$UnitString = 'mg/m^3 d'">mg/m^3 d</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per square meter per day'">mg/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'mg/m^2 d'">mg/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'volts'">V</xsl:when>
            <xsl:when test="$UnitString = 'V'">V</xsl:when>
            <xsl:when test="$UnitString = 'millivolts'">mV</xsl:when>
            <xsl:when test="$UnitString = 'mV'">mV</xsl:when>
            <xsl:when test="$UnitString = 'kilopascal'">kPa</xsl:when>
            <xsl:when test="$UnitString = 'kPa'">kPa</xsl:when>
            <xsl:when test="$UnitString = 'megapascal'">MPa</xsl:when>
            <xsl:when test="$UnitString = 'MPa'">MPa</xsl:when>
            <xsl:when test="$UnitString = 'becquerel'">Bq</xsl:when>
            <xsl:when test="$UnitString = 'Bq'">Bq</xsl:when>
            <xsl:when test="$UnitString = 'becquerels per gram'">Bq/g</xsl:when>
            <xsl:when test="$UnitString = 'Bq/g'">Bq/g</xsl:when>
            <xsl:when test="$UnitString = 'curie'">Ci</xsl:when>
            <xsl:when test="$UnitString = 'Ci'">Ci</xsl:when>
            <xsl:when test="$UnitString = 'picocurie'">pCi</xsl:when>
            <xsl:when test="$UnitString = 'pCi'">pCi</xsl:when>
            <xsl:when test="$UnitString = 'ohm'">ohm</xsl:when>
            <xsl:when test="$UnitString = 'ohm'">ohm</xsl:when>
            <xsl:when test="$UnitString = 'ohm meter'">ohm m</xsl:when>
            <xsl:when test="$UnitString = 'ohm m'">ohm m</xsl:when>
            <xsl:when test="$UnitString = 'picocuries per gram'">pCi/g</xsl:when>
            <xsl:when test="$UnitString = 'pCi/g'">pCi/g</xsl:when>
            <xsl:when test="$UnitString = 'picocuries per liter'">pCi/L</xsl:when>
            <xsl:when test="$UnitString = 'pCi/L'">pCi/L</xsl:when>
            <xsl:when test="$UnitString = 'picocuries per milliliter'">pCi/ml</xsl:when>
            <xsl:when test="$UnitString = 'pCi/ml'">pCi/ml</xsl:when>
            <xsl:when test="$UnitString = 'hour minute'">hhmm</xsl:when>
            <xsl:when test="$UnitString = 'hhmm'">hhmm</xsl:when>
            <xsl:when test="$UnitString = 'year month day'">yymmdd</xsl:when>
            <xsl:when test="$UnitString = 'yymmdd'">yymmdd</xsl:when>
            <xsl:when test="$UnitString = 'year day (Julian)'">yyddd</xsl:when>
            <xsl:when test="$UnitString = 'yyddd'">yyddd</xsl:when>
            <xsl:when test="$UnitString = 'inches per day'">in/d</xsl:when>
            <xsl:when test="$UnitString = 'in/d'">in/d</xsl:when>
            <xsl:when test="$UnitString = 'inches per week'">in/week</xsl:when>
            <xsl:when test="$UnitString = 'in/week'">in/week</xsl:when>
            <xsl:when test="$UnitString = 'inches per storm'">in/storm</xsl:when>
            <xsl:when test="$UnitString = 'in/storm'">in/storm</xsl:when>
            <xsl:when test="$UnitString = 'thousand acre feet'">10^3 ac ft</xsl:when>
            <xsl:when test="$UnitString = '10^3 ac ft'">10^3 ac ft</xsl:when>
            <xsl:when test="$UnitString = 'milliliter'">ml</xsl:when>
            <xsl:when test="$UnitString = 'ml'">ml</xsl:when>
            <xsl:when test="$UnitString = 'cubic feet per second days'">cfs d</xsl:when>
            <xsl:when test="$UnitString = 'cfs d'">cfs d</xsl:when>
            <xsl:when test="$UnitString = 'thousand gallons'">10^3 gal</xsl:when>
            <xsl:when test="$UnitString = '10^3 gal'">10^3 gal</xsl:when>
            <xsl:when test="$UnitString = 'million gallons'">10^6 gal</xsl:when>
            <xsl:when test="$UnitString = '10^6 gal'">10^6 gal</xsl:when>
            <xsl:when test="$UnitString = 'microsiemens per centimeter'">uS/cm</xsl:when>
            <xsl:when test="$UnitString = 'uS/cm'">uS/cm</xsl:when>
            <xsl:when test="$UnitString = 'practical salinity units '">psu</xsl:when>
            <xsl:when test="$UnitString = 'psu'">psu</xsl:when>
            <xsl:when test="$UnitString = 'decibel'">dB</xsl:when>
            <xsl:when test="$UnitString = 'dB'">dB</xsl:when>
            <xsl:when test="$UnitString = 'cubic centimeters per gram'">cm^3/g</xsl:when>
            <xsl:when test="$UnitString = 'cm^3/g'">cm^3/g</xsl:when>
            <xsl:when test="$UnitString = 'square meters per gram'">m^2/g</xsl:when>
            <xsl:when test="$UnitString = 'm^2/g'">m^2/g</xsl:when>
            <xsl:when test="$UnitString = 'short tons per acre foot'">ton/ac ft</xsl:when>
            <xsl:when test="$UnitString = 'ton/ac ft'">ton/ac ft</xsl:when>
            <xsl:when test="$UnitString = 'grams per cubic centimeter'">g/cm^3</xsl:when>
            <xsl:when test="$UnitString = 'g/cm^3'">g/cm^3</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per liter'">mg/L</xsl:when>
            <xsl:when test="$UnitString = 'mg/L'">mg/L</xsl:when>
            <xsl:when test="$UnitString = 'nanograms per cubic meter'">ng/m^3</xsl:when>
            <xsl:when test="$UnitString = 'ng/m^3'">ng/m^3</xsl:when>
            <xsl:when test="$UnitString = 'nanograms per liter'">ng/L</xsl:when>
            <xsl:when test="$UnitString = 'ng/L'">ng/L</xsl:when>
            <xsl:when test="$UnitString = 'grams per liter'">g/L</xsl:when>
            <xsl:when test="$UnitString = 'g/L'">g/L</xsl:when>
            <xsl:when test="$UnitString = 'micrograms per cubic meter'">ug/m^3</xsl:when>
            <xsl:when test="$UnitString = 'ug/m^3'">ug/m^3</xsl:when>
            <xsl:when test="$UnitString = 'micrograms per liter'">ug/L</xsl:when>
            <xsl:when test="$UnitString = 'ug/L'">ug/L</xsl:when>
            <xsl:when test="$UnitString = 'parts per million'">ppm</xsl:when>
            <xsl:when test="$UnitString = 'ppm'">ppm</xsl:when>
            <xsl:when test="$UnitString = 'parts per billion'">ppb</xsl:when>
            <xsl:when test="$UnitString = 'ppb'">ppb</xsl:when>
            <xsl:when test="$UnitString = 'parts per trillion'">ppt</xsl:when>
            <xsl:when test="$UnitString = 'ppt'">ppt</xsl:when>
            <xsl:when test="$UnitString = 'parts per quintillion'">ppqt</xsl:when>
            <xsl:when test="$UnitString = 'ppqt'">ppqt</xsl:when>
            <xsl:when test="$UnitString = 'parts per quadrillion'">ppq</xsl:when>
            <xsl:when test="$UnitString = 'ppq'">ppq</xsl:when>
            <xsl:when test="$UnitString = 'per mille'">%o</xsl:when>
            <xsl:when test="$UnitString = '%o'">%o</xsl:when>
            <xsl:when test="$UnitString = 'microequivalents per liter'">ueq/L</xsl:when>
            <xsl:when test="$UnitString = 'ueq/L'">ueq/L</xsl:when>
            <xsl:when test="$UnitString = 'milliequivalents per liter'">meq/L</xsl:when>
            <xsl:when test="$UnitString = 'meq/L'">meq/L</xsl:when>
            <xsl:when test="$UnitString = 'milliequivalents per 100 gram'">meq/100 g</xsl:when>
            <xsl:when test="$UnitString = 'meq/100 g'">meq/100 g</xsl:when>
            <xsl:when test="$UnitString = 'milliosmols per kilogram'">mOsm/kg</xsl:when>
            <xsl:when test="$UnitString = 'mOsm/kg'">mOsm/kg</xsl:when>
            <xsl:when test="$UnitString = 'nanomoles per liter'">nmol/L</xsl:when>
            <xsl:when test="$UnitString = 'nmol/L'">nmol/L</xsl:when>
            <xsl:when test="$UnitString = 'picograms per cubic meter'">pg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'pg/m^3'">pg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'picograms per liter'">pg/L</xsl:when>
            <xsl:when test="$UnitString = 'pg/L'">pg/L</xsl:when>
            <xsl:when test="$UnitString = 'picograms per milliliter'">pg/ml</xsl:when>
            <xsl:when test="$UnitString = 'pg/ml'">pg/ml</xsl:when>
            <xsl:when test="$UnitString = 'tritium units'">TU</xsl:when>
            <xsl:when test="$UnitString = 'TU'">TU</xsl:when>
            <xsl:when test="$UnitString = 'jackson turbidity units'">JTU</xsl:when>
            <xsl:when test="$UnitString = 'JTU'">JTU</xsl:when>
            <xsl:when test="$UnitString = 'nephelometric turbidity units'">NTU</xsl:when>
            <xsl:when test="$UnitString = 'NTU'">NTU</xsl:when>
            <xsl:when test="$UnitString = 'nephelometric turbidity multibeam unit'">NTMU</xsl:when>
            <xsl:when test="$UnitString = 'NTMU'">NTMU</xsl:when>
            <xsl:when test="$UnitString = 'nephelometric turbidity ratio unit'">NTRU</xsl:when>
            <xsl:when test="$UnitString = 'NTRU'">NTRU</xsl:when>
            <xsl:when test="$UnitString = 'formazin nephelometric multibeam unit'">FNMU</xsl:when>
            <xsl:when test="$UnitString = 'FNMU'">FNMU</xsl:when>
            <xsl:when test="$UnitString = 'formazin nephelometric ratio unit'">FNRU</xsl:when>
            <xsl:when test="$UnitString = 'FNRU'">FNRU</xsl:when>
            <xsl:when test="$UnitString = 'formazin nephelometric unit'">FNU</xsl:when>
            <xsl:when test="$UnitString = 'FNU'">FNU</xsl:when>
            <xsl:when test="$UnitString = 'formazin attenuation unit'">FAU</xsl:when>
            <xsl:when test="$UnitString = 'FAU'">FAU</xsl:when>
            <xsl:when test="$UnitString = 'formazin backscatter unit '">FBU</xsl:when>
            <xsl:when test="$UnitString = 'FBU'">FBU</xsl:when>
            <xsl:when test="$UnitString = 'backscatter units'">BU</xsl:when>
            <xsl:when test="$UnitString = 'BU'">BU</xsl:when>
            <xsl:when test="$UnitString = 'attenuation units'">AU</xsl:when>
            <xsl:when test="$UnitString = 'AU'">AU</xsl:when>
            <xsl:when test="$UnitString = 'platinum cobalt units'">PCU</xsl:when>
            <xsl:when test="$UnitString = 'PCU'">PCU</xsl:when>
            <xsl:when test="$UnitString = 'the ratio between UV absorbance at 254 nm and DOC level'"
                >L/(mg DOC/cm)</xsl:when>
            <xsl:when test="$UnitString = 'L/(mg DOC/cm)'">L/(mg DOC/cm)</xsl:when>
            <xsl:when test="$UnitString = 'billion colonies per day'">10^9 colonies/d</xsl:when>
            <xsl:when test="$UnitString = '10^9 colonies/d'">10^9 colonies/d</xsl:when>
            <xsl:when test="$UnitString = 'number of organisms per square meter'">#/m^2</xsl:when>
            <xsl:when test="$UnitString = '#/m^2'">#/m^2</xsl:when>
            <xsl:when test="$UnitString = 'number of organisms per liter'">#/L</xsl:when>
            <xsl:when test="$UnitString = '#/L'">#/L</xsl:when>
            <xsl:when test="$UnitString = 'number or organisms per cubic meter'">#/m^3</xsl:when>
            <xsl:when test="$UnitString = '#/m^3'">#/m^3</xsl:when>
            <xsl:when test="$UnitString = 'cells per milliliter'">cells/ml</xsl:when>
            <xsl:when test="$UnitString = 'cells/ml'">cells/ml</xsl:when>
            <xsl:when test="$UnitString = 'cells per square millimeter'">cells/mm^2</xsl:when>
            <xsl:when test="$UnitString = 'cells/mm^2'">cells/mm^2</xsl:when>
            <xsl:when test="$UnitString = 'colonies per 100 milliliters'">colonies/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'colonies/100 ml'">colonies/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'colonies per milliliter'">colonies/ml</xsl:when>
            <xsl:when test="$UnitString = 'colonies/ml'">colonies/ml</xsl:when>
            <xsl:when test="$UnitString = 'colonies per gram'">colonies/g</xsl:when>
            <xsl:when test="$UnitString = 'colonies/g'">colonies/g</xsl:when>
            <xsl:when test="$UnitString = 'colony forming units per milliliter'">CFU/ml</xsl:when>
            <xsl:when test="$UnitString = 'CFU/ml'">CFU/ml</xsl:when>
            <xsl:when test="$UnitString = 'cysts per 10 liters'">cysts/10 L</xsl:when>
            <xsl:when test="$UnitString = 'cysts/10 L'">cysts/10 L</xsl:when>
            <xsl:when test="$UnitString = 'cysts per 100 liters'">cysts/100 L</xsl:when>
            <xsl:when test="$UnitString = 'cysts/100 L'">cysts/100 L</xsl:when>
            <xsl:when test="$UnitString = 'oocysts per 10 liters'">oocysts/10 L</xsl:when>
            <xsl:when test="$UnitString = 'oocysts/10 L'">oocysts/10 L</xsl:when>
            <xsl:when test="$UnitString = 'oocysts per 100 liters'">oocysts/100 L</xsl:when>
            <xsl:when test="$UnitString = 'oocysts/100 L'">oocysts/100 L</xsl:when>
            <xsl:when test="$UnitString = 'most probable number'">MPN</xsl:when>
            <xsl:when test="$UnitString = 'MPN'">MPN</xsl:when>
            <xsl:when test="$UnitString = 'most probable number per 100 liters'">MPN/100
                L</xsl:when>
            <xsl:when test="$UnitString = 'MPN/100 L'">MPN/100 L</xsl:when>
            <xsl:when test="$UnitString = 'most probable number per 100 milliliters'">MPN/100
                ml</xsl:when>
            <xsl:when test="$UnitString = 'MPN/100 ml'">MPN/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'most probable number per gram'">MPN/g</xsl:when>
            <xsl:when test="$UnitString = 'MPN/g'">MPN/g</xsl:when>
            <xsl:when test="$UnitString = 'plaque-forming units per 100 liters'">PFU/100
                L</xsl:when>
            <xsl:when test="$UnitString = 'PFU/100 L'">PFU/100 L</xsl:when>
            <xsl:when test="$UnitString = 'plaques per 100 milliliters'">plaques/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'plaques/100 ml'">plaques/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'counts per second'">#/s</xsl:when>
            <xsl:when test="$UnitString = '#/s'">#/s</xsl:when>
            <xsl:when test="$UnitString = 'per day'">1/d</xsl:when>
            <xsl:when test="$UnitString = '1/d'">1/d</xsl:when>
            <xsl:when test="$UnitString = 'nanograms per square meter per hour'">ng/m^2
                hr</xsl:when>
            <xsl:when test="$UnitString = 'ng/m^2 hr'">ng/m^2 hr</xsl:when>
            <xsl:when test="$UnitString = 'nanograms per square meter per week'">ng/m^2
                week</xsl:when>
            <xsl:when test="$UnitString = 'ng/m^2 week'">ng/m^2 week</xsl:when>
            <xsl:when test="$UnitString = 'count'">#</xsl:when>
            <xsl:when test="$UnitString = '#'">#</xsl:when>
            <xsl:when test="$UnitString = 'categorical'">code</xsl:when>
            <xsl:when test="$UnitString = 'code'">code</xsl:when>
            <xsl:when test="$UnitString = 'absorbance per centimeter per mg/L of given acid '"
                >100/cm mg/L</xsl:when>
            <xsl:when test="$UnitString = '100/cm mg/L'">100/cm mg/L</xsl:when>
            <xsl:when test="$UnitString = 'per liter'">1/L</xsl:when>
            <xsl:when test="$UnitString = '1/L'">1/L</xsl:when>
            <xsl:when test="$UnitString = 'per mille per hour'">%o/hr</xsl:when>
            <xsl:when test="$UnitString = '%o/hr'">%o/hr</xsl:when>
            <xsl:when test="$UnitString = 'gallons per batch'">gpb</xsl:when>
            <xsl:when test="$UnitString = 'gpb'">gpb</xsl:when>
            <xsl:when test="$UnitString = 'cubic feet per barrel'">ft^3/bbl</xsl:when>
            <xsl:when test="$UnitString = 'ft^3/bbl'">ft^3/bbl</xsl:when>
            <xsl:when test="$UnitString = 'per mille by volume'">%o by vol</xsl:when>
            <xsl:when test="$UnitString = '%o by vol'">%o by vol</xsl:when>
            <xsl:when test="$UnitString = 'per mille per hour by volume'">%o/hr by vol</xsl:when>
            <xsl:when test="$UnitString = '%o/hr by vol'">%o/hr by vol</xsl:when>
            <xsl:when test="$UnitString = 'micromoles'">umol</xsl:when>
            <xsl:when test="$UnitString = 'umol'">umol</xsl:when>
            <xsl:when test="$UnitString = 'tons of calcium carbonate per kiloton'"
                >tCaCO3/Kt</xsl:when>
            <xsl:when test="$UnitString = 'tCaCO3/Kt'">tCaCO3/Kt</xsl:when>
            <xsl:when test="$UnitString = 'siemens per meter'">S/m</xsl:when>
            <xsl:when test="$UnitString = 'S/m'">S/m</xsl:when>
            <xsl:when test="$UnitString = 'millisiemens per centimeter'">mS/cm</xsl:when>
            <xsl:when test="$UnitString = 'mS/cm'">mS/cm</xsl:when>
            <xsl:when test="$UnitString = 'siemens per centimeter'">S/cm</xsl:when>
            <xsl:when test="$UnitString = 'S/cm'">S/cm</xsl:when>
            <xsl:when test="$UnitString = 'practical salinity scale'">pss</xsl:when>
             <xsl:when test="$UnitString = 'pss'">pss</xsl:when>
           <xsl:when test="$UnitString = 'per meter'">1/m</xsl:when>
            <xsl:when test="$UnitString = '1/m'">1/m</xsl:when>
            <xsl:when test="$UnitString = 'normal'">N</xsl:when>
            <xsl:when test="$UnitString = 'N'">N</xsl:when>
            <xsl:when test="$UnitString = 'nanomoles per kilogram'">nmol/kg</xsl:when>
            <xsl:when test="$UnitString = 'nmol/kg'">nmol/kg</xsl:when>
            <xsl:when test="$UnitString = 'millimoles per kilogram'">mmol/kg</xsl:when>
           <xsl:when test="$UnitString = 'mmol/kg'">mmol/kg</xsl:when>
            <xsl:when test="$UnitString = 'millimoles per square meter per hour'">mmol/m^2
                hr</xsl:when>
            <xsl:when test="$UnitString = 'mmol/m^2 hr'">mmol/m^2 hr</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per cubic meter per hour'">mg/m^3
                hr</xsl:when>
            <xsl:when test="$UnitString = 'mg/m^3 hr'">mg/m^3 hr</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per day'">mg/d</xsl:when>
            <xsl:when test="$UnitString = 'mg/d'">mg/d</xsl:when>
            <xsl:when test="$UnitString = 'liters per minute'">L/min</xsl:when>
            <xsl:when test="$UnitString = 'L/min'">L/min</xsl:when>
            <xsl:when test="$UnitString = 'liters per day'">L/d</xsl:when>
            <xsl:when test="$UnitString = 'L/d'">L/d</xsl:when>
            <xsl:when test="$UnitString = 'jackson candle units '">JCU</xsl:when>
            <xsl:when test="$UnitString = 'JCU'">JCU</xsl:when>
            <xsl:when test="$UnitString = 'grains per gallon'">gpg</xsl:when>
            <xsl:when test="$UnitString = 'gpg'">gpg</xsl:when>
            <xsl:when test="$UnitString = 'gallons per second'">gps</xsl:when>
            <xsl:when test="$UnitString = 'gps'">gps</xsl:when>
            <xsl:when test="$UnitString = 'gallons per hour'">gph</xsl:when>
            <xsl:when test="$UnitString = 'gph'">gph</xsl:when>
            <xsl:when test="$UnitString = 'foot candle'">ftc</xsl:when>
            <xsl:when test="$UnitString = 'ftc'">ftc</xsl:when>
            <xsl:when test="$UnitString = 'fibers per liter'">fibers/L</xsl:when>
            <xsl:when test="$UnitString = 'fibers/L'">fibers/L</xsl:when>
            <xsl:when test="$UnitString = 'drips per minute'">drips/min</xsl:when>
            <xsl:when test="$UnitString = 'drips/min'">drips/min</xsl:when>
            <xsl:when test="$UnitString = 'cubic centimeters per second'">cm^3/sec</xsl:when>
            <xsl:when test="$UnitString = 'cm^3/sec'">cm^3/sec</xsl:when>
            <xsl:when test="$UnitString = 'colony forming units'">CFU</xsl:when>
            <xsl:when test="$UnitString = 'CFU'">CFU</xsl:when>
            <xsl:when test="$UnitString = 'colony forming units per 100 milliliter'">CFU/100
                ml</xsl:when>
            <xsl:when test="$UnitString = 'CFU/100 ml'">CFU/100 ml</xsl:when>
            <xsl:when test="$UnitString = 'cubic feet per minute'">cfm</xsl:when>
            <xsl:when test="$UnitString = 'cfm'">cfm</xsl:when>
            <xsl:when test="$UnitString = 'ADMI color unit'">ADMI</xsl:when>
            <xsl:when test="$UnitString = 'ADMI'">ADMI</xsl:when>
            <xsl:when test="$UnitString = 'percent by volume'">% by vol</xsl:when>
            <xsl:when test="$UnitString = '% by vol'">% by vol</xsl:when>
            <xsl:when test="$UnitString = 'number of organisms per 500 milliliter'">#/500
                ml</xsl:when>
            <xsl:when test="$UnitString = '#/500 ml'">#/500 ml</xsl:when>
            <xsl:when test="$UnitString = 'number of organisms per 100 gallon'">#/100 gal</xsl:when>
            <xsl:when test="$UnitString = '#/100 gal'">#/100 gal</xsl:when>
            <xsl:when test="$UnitString = 'grams per cubic meter per hour'">g/m^3 hr</xsl:when>
            <xsl:when test="$UnitString = 'g/m^3 hr'">g/m^3 hr</xsl:when>
            <xsl:when test="$UnitString = 'grams per minute'">g/min</xsl:when>
            <xsl:when test="$UnitString = 'g/min'">g/min</xsl:when>
            <xsl:when test="$UnitString = 'grams per second'">g/s</xsl:when>
            <xsl:when test="$UnitString = 'g/s'">g/s</xsl:when>
            <xsl:when test="$UnitString = 'million cubic feet'">10^6 ft^3</xsl:when>
            <xsl:when test="$UnitString = '10^6 ft^3'">10^6 ft^3</xsl:when>
            <xsl:when test="$UnitString = 'month year'">mmyy</xsl:when>
            <xsl:when test="$UnitString = 'mmyy'">mmyy</xsl:when>
            <xsl:when test="$UnitString = 'bar'">bar</xsl:when>
            <xsl:when test="$UnitString = 'bar'">bar</xsl:when>
            <xsl:when test="$UnitString = 'decisiemens per centimeter'">dS/cm</xsl:when>
            <xsl:when test="$UnitString = 'dS/cm'">dS/cm</xsl:when>
            <xsl:when test="$UnitString = 'micromoles per liter'">umol/L</xsl:when>
            <xsl:when test="$UnitString = 'umol/L'">umol/L</xsl:when>
            <xsl:when test="$UnitString = 'Joules per square centimeter'">J/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'J/cm^2'">J/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'millimeters per day'">mm/day</xsl:when>
            <xsl:when test="$UnitString = 'mm/day'">mm/day</xsl:when>
            <xsl:when test="$UnitString = 'parts per thousand'">ppth</xsl:when>
            <xsl:when test="$UnitString = 'ppth'">ppth</xsl:when>
            <xsl:when test="$UnitString = 'megaliter'">ML</xsl:when>
            <xsl:when test="$UnitString = 'ML'">ML</xsl:when>
            <xsl:when test="$UnitString = 'Percent Saturation'">% Sat</xsl:when>
            <xsl:when test="$UnitString = '% Sat'">% Sat</xsl:when>
            <xsl:when test="$UnitString = 'pH Unit'">pH</xsl:when>
            <xsl:when test="$UnitString = 'pH'">pH</xsl:when>
            <xsl:when test="$UnitString = 'millimeters per second'">mm/s</xsl:when>
            <xsl:when test="$UnitString = 'mm/s'">mm/s</xsl:when>
            <xsl:when test="$UnitString = 'liters per hour'">L/hr</xsl:when>
            <xsl:when test="$UnitString = 'L/hr'">L/hr</xsl:when>
            <xsl:when test="$UnitString = 'cubic hecto meter'">(hm)^3</xsl:when>
            <xsl:when test="$UnitString = '(hm)^3'">(hm)^3</xsl:when>
            <xsl:when test="$UnitString = 'mols per cubic meter'">mol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'mol/m^3'">mol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'kilo grams per month'">kg/month</xsl:when>
            <xsl:when test="$UnitString = 'kg/month'">kg/month</xsl:when>
            <xsl:when test="$UnitString = 'Hecto Pascal'">hPa</xsl:when>
            <xsl:when test="$UnitString = 'hPa'">hPa</xsl:when>
            <xsl:when test="$UnitString = 'kilo grams per cubic meter'">kg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'kg/m^3'">kg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'short tons per month'">ton/month</xsl:when>
            <xsl:when test="$UnitString = 'ton/month'">ton/month</xsl:when>
            <xsl:when test="$UnitString = 'grams per square meter per hour'">g/m^2 hr</xsl:when>
            <xsl:when test="$UnitString = 'g/m^2 hr'">g/m^2 hr</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per cubic meter'">mg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'mg/m^3'">mg/m^3</xsl:when>
            <xsl:when test="$UnitString = 'meters squared per second squared'">m^2/s^2</xsl:when>
            <xsl:when test="$UnitString = 'm^2/s^2'">m^2/s^2</xsl:when>
            <xsl:when test="$UnitString = 'squared degree Celsius'">(DegC)^2</xsl:when>
            <xsl:when test="$UnitString = '(DegC)^2'">(DegC)^2</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per cubic meter squared'"
                >(mg/m^3)^2</xsl:when>
            <xsl:when test="$UnitString = '(mg/m^3)^2'">(mg/m^3)^2</xsl:when>
            <xsl:when test="$UnitString = 'meters per second degree Celsius'">m/s DegC</xsl:when>
            <xsl:when test="$UnitString = 'm/s DegC'">m/s DegC</xsl:when>
            <xsl:when test="$UnitString = 'millimoles per square meter per second'">mmol/m^2
                s</xsl:when>
            <xsl:when test="$UnitString = 'mmol/m^2 s'">mmol/m^2 s</xsl:when>
            <xsl:when test="$UnitString = 'degree Celsius millimoles per cubic meter'">DegC
                mmol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'DegC mmol/m^3'">DegC mmol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'millimoles per cubic meter'">mmol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'mmol/m^3'">mmol/m^3</xsl:when>
            <xsl:when test="$UnitString = 'millimoles per cubic meter squared'"
                >(mmol/m^3)^2</xsl:when>
            <xsl:when test="$UnitString = '(mmol/m^3)^2'">(mmol/m^3)^2</xsl:when>
            <xsl:when test="$UnitString = 'Langleys per hour'">Ly/hr</xsl:when>
            <xsl:when test="$UnitString = 'Ly/hr'">Ly/hr</xsl:when>
            <xsl:when test="$UnitString = 'hits per square centimeter'">hits/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'hits/cm^2'">hits/cm^2</xsl:when>
            <xsl:when test="$UnitString = 'hits per square centimeter per hour'">hits/cm^2
                hr</xsl:when>
            <xsl:when test="$UnitString = 'hits/cm^2 hr'">hits/cm^2 hr</xsl:when>
            <xsl:when test="$UnitString = 'relative fluorescence units'">RFU</xsl:when>
            <xsl:when test="$UnitString = 'RFU'">RFU</xsl:when>
            <xsl:when test="$UnitString = 'kilograms per hectare per day'">kg/ha d</xsl:when>
            <xsl:when test="$UnitString = 'kg/ha d'">kg/ha d</xsl:when>
            <xsl:when test="$UnitString = 'kilowatts per square meter'">kW/m^2</xsl:when>
            <xsl:when test="$UnitString = 'kW/m^2'">kW/m^2</xsl:when>
            <xsl:when test="$UnitString = 'kilograms per square meter'">kg/m^2</xsl:when>
            <xsl:when test="$UnitString = 'kg/m^2'">kg/m^2</xsl:when>
            <xsl:when test="$UnitString = 'microeinsteins per square meter per day'">uE/m^2
                d</xsl:when>
            <xsl:when test="$UnitString = 'uE/m^2 d'">uE/m^2 d</xsl:when>
            <xsl:when test="$UnitString = 'microgram per milliliter'">ug/mL</xsl:when>
            <xsl:when test="$UnitString = 'ug/mL'">ug/mL</xsl:when>
            <xsl:when test="$UnitString = 'Newton per square meter'">Newton/m^2</xsl:when>
            <xsl:when test="$UnitString = 'Newton/m^2'">Newton/m^2</xsl:when>
            <xsl:when test="$UnitString = 'micromoles per liter per hour'">umol/L hr</xsl:when>
            <xsl:when test="$UnitString = 'umol/L hr'">umol/L hr</xsl:when>
              <xsl:when test="$UnitString = 'decisiemens per meter'">dS/m</xsl:when>
            <xsl:when test="$UnitString = 'dS/m'">dS/m</xsl:when>
            <xsl:when test="$UnitString = 'milligrams per kilogram'">mg/Kg</xsl:when>
            <xsl:when test="$UnitString = 'mg/Kg'">mg/Kg</xsl:when>
               <xsl:when test="$UnitString = 'number of organisms per 100 milliliter'">#/100
                mL</xsl:when>
            <xsl:when test="$UnitString = '#/100 mL'">#/100 mL</xsl:when>
            <xsl:when test="$UnitString = 'micrograms per kilogram'">ug/Kg</xsl:when>
            <xsl:when test="$UnitString = 'ug/Kg'">ug/Kg</xsl:when>
            <xsl:when test="$UnitString = 'grams per kilogram'">g/Kg</xsl:when>
          <xsl:when test="$UnitString = 'g/Kg'">g/Kg</xsl:when>
      </xsl:choose>
       
    </xsl:template>
-->
</xsl:stylesheet>
