generateBagIt {
# -----------------------------------------------------
# generateBagIt for HydroShare
# adapted by Hong Yi on May 2015 to fit HydroShare use case 
# from rulegenerateBagIt.r originally developed by Terrell 
# Russell on August 2010
# -----------------------------------------------------
#
#  University of North Carolina at Chapel Hill
#  - Requires iRODS 2.4.1
#  - Conforms to BagIt Spec v0.96
#
# -----------------------------------------------------
#
### - use the input BAGITDATA directory to generate bagit 
###   files in place without creating new bagit root directory
### - writes bagit.txt to BAGITDATA/bagit.txt
### - generates payload manifest file of BAGITDATA/data
### - writes payload manifest to BAGITDATA/manifest-md5.txt
### - writes tagmanifest file to BAGITDATA/tagmanifest-md5.txt
### - writes to rodsLog
#
# -----------------------------------------------------

  ### - writes bagit.txt to NEWBAGITROOT/bagit.txt
  writeLine("stdout","BagIt-Version: 0.96");
  writeLine("stdout","Tag-File-Character-Encoding: UTF-8");
  msiDataObjCreate("*BAGITDATA" ++ "/bagit.txt","forceFlag=",*FD);
  msiDataObjWrite(*FD,"stdout",*WLEN);
  msiDataObjClose(*FD,*Status);
  msiFreeBuffer("stdout");

  ### - generates payload manifest file of BAGITDATA/data
  msiStrlen(*BAGITDATA,*ROOTLENGTH);
  *OFFSET = int(*ROOTLENGTH) + 1;
  *NEWBAGITDATA = "*BAGITDATA" ++ "/data";
  *ContInxOld = 1;
  *Condition = "COLL_NAME like '*NEWBAGITDATA%%'";
  msiMakeGenQuery("DATA_ID, DATA_NAME, COLL_NAME",*Condition,*GenQInp);
  msiExecGenQuery(*GenQInp, *GenQOut);
  msiGetContInxFromGenQueryOut(*GenQOut,*ContInxNew);
  while(*ContInxOld > 0) {
    foreach(*GenQOut) {
       msiGetValByKey(*GenQOut, "DATA_NAME", *Object);
       msiGetValByKey(*GenQOut, "COLL_NAME", *Coll);
       *FULLPATH = "*Coll" ++ "/" ++ "*Object";
       msiDataObjChksum(*FULLPATH, "forceChksum=", *CHKSUM);
       msiSubstr(*FULLPATH,str(*OFFSET),"null",*RELATIVEPATH);
       writeString("stdout", *RELATIVEPATH);
       writeLine("stdout","   *CHKSUM")
    }
    *ContInxOld = *ContInxNew;
    if(*ContInxOld > 0) {msiGetMoreRows(*GenQInp,*GenQOut,*ContInxNew);}
  }

  ### - writes payload manifest to BAGITDATA/manifest-md5.txt
  msiDataObjCreate("*BAGITDATA" ++ "/manifest-md5.txt","forceFlag=",*FD);
  msiDataObjWrite(*FD,"stdout",*WLEN);
  msiDataObjClose(*FD,*Status);
  msiFreeBuffer("stdout");

  ### - writes tagmanifest file to BAGITDATA/tagmanifest-md5.txt
  writeString("stdout","bagit.txt    ");
  msiDataObjChksum("*BAGITDATA" ++ "/bagit.txt","forceChksum",*CHKSUM);
  writeLine("stdout",*CHKSUM);
  writeString("stdout","manifest-md5.txt    ");
  msiDataObjChksum("*BAGITDATA" ++ "/manifest-md5.txt","forceChksum",*CHKSUM);
  writeLine("stdout",*CHKSUM);
  msiDataObjCreate("*BAGITDATA" ++ "/tagmanifest-md5.txt","forceFlag=",*FD);
  msiDataObjWrite(*FD,"stdout",*WLEN);
  msiDataObjClose(*FD,*Status);
  msiFreeBuffer("stdout");

  ### - writes to rodsLog
  msiWriteRodsLog("BagIt bag files created in place: *BAGITDATA <- *BAGITDATA",*Status);
}
INPUT *BAGITDATA="/dummy/dummy/dummy" 
OUTPUT ruleExecOut
