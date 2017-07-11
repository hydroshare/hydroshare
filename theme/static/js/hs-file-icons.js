/**
* Created by Mauriel on 3/18/2017.
*/

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

    fileIcons.JS = fileIcons.PY = fileIcons.PHP = fileIcons.JAVA = fileIcons.CS =
        "<span class='fb-file-icon fa " + "fa-file-code-o" + "'></span>";

    fileIcons.SHP =
        "<span class='fa-stack fb-stack fb-stack-shape'>" +
        "<i class='fa fa-file-o fa-stack-2x'></i>" +
        "<i class='fa fa-globe fa-stack-1x'></i>" +
        "</span>";

    fileIcons.SQLITE =
        "<span class='fa-stack fb-stack fb-stack-database'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-database fa-stack-1x'></i>" +
        "</span>";

    fileIcons.NC =
        "<span class='fa-stack fb-stack fb-stack-netcdf'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-th-large fa-stack-1x'></i>" +
        "</span>";

    fileIcons.REFTS =
        "<span class='fa-stack fb-stack fb-stack-refts'>" +
        "<i class='fa fa-file-o fa-stack-2x '></i>" +
        "<i class='fa fa-line-chart fa-stack-1x'></i>" +
        "</span>";

    fileIcons.DEFAULT =
        "<span class='fb-file-icon fa fa-file-o'></span>";


    return fileIcons;
}
