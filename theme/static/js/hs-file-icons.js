/**
* Created by Mauriel on 3/18/2017.
*/
function getFolderIcons() {
    var folderIcons = {};
    folderIcons.GeoRasterLogicalFile =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/geographicraster48x48.png' " +
        "alt='Geographic Raster Aggregation Icon'/></span>";

    folderIcons.NetCDFLogicalFile =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/multidimensional48x48.png' " +
        "alt='MultiDimensional (NetCDF) Aggregation Icon'/></span>";

    folderIcons.TimeSeriesLogicalFile =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/timeseries48x48.png' " +
        "alt='Time Series Aggregation Icon'/></span>";

    folderIcons.RefTimeseriesLogicalFile =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/his48x48.png' " +
        "alt='HIS Referenced Time Series Aggregation Icon'/></span>";

    folderIcons.GeoFeatureLogicalFile =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/geographicfeature48x48.png' " +
        "alt='Geographic Feature Aggregation Icon'/></span>";

    folderIcons.DEFAULT =
        "<span class='fb-aggregation-icon'>" +
        "<img src='/static/img/resource-icons/composite48x48.png' " +
        "alt='Default Aggregation Icon'/></span>";
    return folderIcons;
}

function getFileIcons() {
    var fileIcons = {};
    fileIcons.PDF =
        "<span class='fb-file-icon fa " + "fa-file-pdf-o" + "'></span>";

    fileIcons.XLS = fileIcons.XLT = fileIcons.XML = fileIcons.CSV = fileIcons.XLSX =
        "<span class='fb-file-icon fa " + "fa-file-excel-o" + "'></span>";

    fileIcons.ZIP = fileIcons.ZIP = fileIcons.RAR5 =
        "<span class='fb-file-icon fa " + "fa-file-zip-o" + "'></span>";

    fileIcons.DOC = fileIcons.DOCX =
        "<span class='fb-file-icon fa " + "fa-file-word-o" + "'></span>";

    fileIcons.MP3 = fileIcons.WAV = fileIcons.WMA =
        "<span class='fb-file-icon fa " + "fa-file-audio-o" + "'></span>";

    fileIcons.MP4 = fileIcons.MOV = fileIcons.WMV =
        "<span class='fb-file-icon fa " + "fa-file-movie-o" + "'></span>";

    fileIcons.PNG = fileIcons.JPG = fileIcons.JPEG = fileIcons.GIF = fileIcons.TIF = fileIcons.BMP =
        "<span class='fb-file-icon fa " + "fa-file-image-o" + "'></span>";

    fileIcons.TXT =
        "<span class='fb-file-icon fa " + "fa-file-text-o" + "'></span>";

    fileIcons.PPT = fileIcons.PPTX =
        "<span class='fb-file-icon fa " + "fa-file-powerpoint-o" + "'></span>";

    fileIcons.PHP = fileIcons.H =
        "<span class='fb-file-icon fa " + "fa-file-code-o" + "'></span>";

    fileIcons.PY = fileIcons.P = fileIcons.PYC  =
        "<span class='fa-stack fb-stack fb-stack-py'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-python fa-stack-1x'></i>" +
        "</span>";

   fileIcons.IPYNB  =
        "<span class='fa-stack fb-stack fb-stack-py fb-stack-ipynb'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-python fa-stack-1x'></i>" +
        "</span>";

    fileIcons.SHP =
        "<span class='fa-stack fb-stack fb-stack-shape'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i class='fa fa-globe fa-stack-1x'></i>" +
        "</span>";

    fileIcons.JS =
        "<span class='fa-stack fb-stack fb-stack-js'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-javascript-alt fa-stack-1x'></i>" +
        "</span>";

    fileIcons.CPP = fileIcons.CC = fileIcons.CXX = fileIcons.CP =
        "<span class='fa-stack fb-stack fb-stack-cpp'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-cplusplus fa-stack-1x'></i>" +
        "</span>";

    fileIcons.C =
        "<span class='fa-stack fb-stack fb-stack-c'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-c fa-stack-1x'></i>" +
        "</span>";

    fileIcons.CSS =
        "<span class='fa-stack fb-stack fb-stack-css'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-css fa-stack-1x'></i>" +
        "</span>";

    fileIcons.HTML = fileIcons.HTM = fileIcons.SHTML = fileIcons.XHTML = fileIcons.TMPL = fileIcons.TPL =
        "<span class='fa-stack fb-stack fb-stack-html'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-html fa-stack-1x'></i>" +
        "</span>";

    fileIcons.CS = fileIcons.CSX =
        "<span class='fa-stack fb-stack fb-stack-cs'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-csharp fa-stack-1x'></i>" +
        "</span>";

    fileIcons.JAVA = fileIcons.JAR = fileIcons.JSP =
        "<span class='fa-stack fb-stack fb-stack-java'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-java-bold fa-stack-1x'></i>" +
        "</span>";

    fileIcons.MYSQL =
        "<span class='fa-stack fb-stack fb-stack-mysql'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i data-icon class='icon-mysql-alt fa-stack-1x'></i>" +
        "</span>";

    fileIcons.SQLITE = fileIcons.SQL =
        "<span class='fa-stack fb-stack fb-stack-database'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-database fa-stack-1x'></i>" +
        "</span>";

    fileIcons.NC =
        "<span class='fa-stack fb-stack fb-stack-netcdf'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-th-large fa-stack-1x'></i>" +
        "</span>";

    // note this is for .refts.json files
    fileIcons.JSON =
        "<span class='fa-stack fb-stack fb-stack-refts'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-line-chart fa-stack-1x'></i>" +
        "</span>";

    fileIcons.DEFAULT =
        "<span class='fb-file-icon fa fa-file-o'></span>";


    return fileIcons;
}
