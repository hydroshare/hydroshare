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
### - writes payload manifest to BAGITDATA/manifest-sha256.txt
### - writes tagmanifest file to BAGITDATA/tagmanifest-sha256.txt
### - writes to rodsLog
#
# -----------------------------------------------------

  ### - writes bagit.txt to NEWBAGITROOT/bagit.txt
  writeLine("stdout", "BagIt-Version: 0.96");
  writeLine("stdout", "Tag-File-Character-Encoding: UTF-8");
  msiDataObjCreate("*BAGITDATA" ++ "/bagit.txt", "destRescName=" ++ "*DESTRESC" ++ "++++forceFlag=", *FD);
  msiDataObjWrite(*FD, "stdout", *WLEN);
  msiDataObjClose(*FD, *Status);
  msiFreeBuffer("stdout");

  ### - generates payload manifest file of BAGITDATA/data
  msiStrlen(*BAGITDATA, *ROOTLENGTH);
  *OFFSET = int(*ROOTLENGTH) + 1;
  *NEWBAGITDATA = "*BAGITDATA" ++ "/data";
  *ContInxOld = 1;
  *Condition = "COLL_NAME like '*NEWBAGITDATA%%'";
  msiMakeGenQuery("DATA_ID, DATA_NAME, COLL_NAME", *Condition, *GenQInp);
  msiExecGenQuery(*GenQInp, *GenQOut);
  msiGetContInxFromGenQueryOut(*GenQOut, *ContInxNew);
  while(*ContInxOld > 0) {
    foreach(*GenQOut) {
      msiGetValByKey(*GenQOut, "DATA_NAME", *Object);
      msiGetValByKey(*GenQOut, "COLL_NAME", *Coll);
      *FULLPATH = "*Coll" ++ "/" ++ "*Object";
      msiDataObjChksum(*FULLPATH, "forceChksum=", *CHKSUM);
      msiSubstr(*FULLPATH,str(*OFFSET), "null", *RELATIVEPATH);
      writeString("stdout", *CHKSUM);
      writeLine("stdout", "    *RELATIVEPATH")
    }
    *ContInxOld = *ContInxNew;
    if(*ContInxOld > 0) {
      msiGetMoreRows(*GenQInp, *GenQOut, *ContInxNew);
    }
  }

  ### - writes payload manifest to BAGITDATA/manifest-sha256.txt
  msiDataObjCreate("*BAGITDATA" ++ "/manifest-sha256.txt", "destRescName=" ++ "*DESTRESC" ++ "++++forceFlag=", *FD);
  msiDataObjWrite(*FD, "stdout", *WLEN);
  msiDataObjClose(*FD, *Status);
  msiFreeBuffer("stdout");

  ### - writes tagmanifest file to BAGITDATA/tagmanifest-sha256.txt
  msiDataObjChksum("*BAGITDATA" ++ "/bagit.txt", "forceChksum", *CHKSUM);
  writeString("stdout", *CHKSUM);
  writeLine("stdout", "    bagit.txt")
  msiDataObjChksum("*BAGITDATA" ++ "/manifest-sha256.txt", "forceChksum", *CHKSUM);
  writeString("stdout", *CHKSUM);
  writeLine("stdout", "    manifest-sha256.txt");
  msiDataObjCreate("*BAGITDATA" ++ "/tagmanifest-sha256.txt", "destRescName=" ++ "*DESTRESC" ++ "++++forceFlag=", *FD);
  msiDataObjWrite(*FD, "stdout", *WLEN);
  msiDataObjClose(*FD, *Status);
  msiFreeBuffer("stdout");

  ### - writes to rodsLog
  msiWriteRodsLog("BagIt bag files created in place: *BAGITDATA <- *BAGITDATA", *Status);
}
INPUT *BAGITDATA="/dummy/dummy/dummy", *DESTRESC="dummy"
OUTPUT ruleExecOut
