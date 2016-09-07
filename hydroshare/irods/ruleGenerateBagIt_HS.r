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
### - files in place without creating new bagit root directory.
### - Note that default hash scheme has to be set to MD5 on
### - both client and server in order for checksum to comply
### - with bagit specification since the default SHA256 hash
### - scheme is base64 encoded, which does not meet hex-encoded
### - requirement for checksums in bagit specification.
### - writes bagit.txt to BAGITDATA/bagit.txt
### - generates payload manifest file of BAGITDATA/data
### - writes payload manifest to BAGITDATA/manifest-md5.txt
### - writes tagmanifest file to BAGITDATA/tagmanifest-md5.txt
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
  msiMakeGenQuery("DATA_ID, DATA_NAME, COLL_NAME, DATA_CHECKSUM", *Condition, *GenQInp);
  msiExecGenQuery(*GenQInp, *GenQOut);
  msiGetContInxFromGenQueryOut(*GenQOut, *ContInxNew);
  while(*ContInxOld > 0) {
    foreach(*GenQOut) {
      msiGetValByKey(*GenQOut, "DATA_NAME", *Object);
      msiGetValByKey(*GenQOut, "COLL_NAME", *Coll);
      msiGetValByKey(*GenQOut, "DATA_CHECKSUM", *CHKSUM);
      ### - only recalculate checksum when the checksum retrieved from iCAT
      ### - is empty or not MD5, but sha256 prefixed which is the default hash scheme
      ### - to accommodate the case that the checksum stored in iCAT might
      ### - be generated before default hash scheme is changed to MD5
      *FULLPATH = "*Coll" ++ "/" ++ "*Object";
      if (strlen(*CHKSUM) > 5) {
        *PrefixStr = substr(*CHKSUM, 0, 5);
        if (*PrefixStr == 'sha2:') {
          msiDataObjChksum(*FULLPATH, "forceChksum=", *CHKSUM);
        }
      }
      else {
        msiDataObjChksum(*FULLPATH, "forceChksum=", *CHKSUM);
      }

      msiSubstr(*FULLPATH, str(*OFFSET), "null", *RELATIVEPATH);
      writeString("stdout", *CHKSUM);
      writeLine("stdout", "    *RELATIVEPATH")
    }
    *ContInxOld = *ContInxNew;
    if(*ContInxOld > 0) {
      msiGetMoreRows(*GenQInp, *GenQOut, *ContInxNew);
    }
  }

  ### - writes payload manifest to BAGITDATA/manifest-md5.txt
  msiDataObjCreate("*BAGITDATA" ++ "/manifest-md5.txt", "destRescName=" ++ "*DESTRESC" ++ "++++forceFlag=", *FD);
  msiDataObjWrite(*FD, "stdout", *WLEN);
  msiDataObjClose(*FD, *Status);
  msiFreeBuffer("stdout");

  ### - writes tagmanifest file to BAGITDATA/tagmanifest-md5.txt
  msiDataObjChksum("*BAGITDATA" ++ "/bagit.txt", "forceChksum", *CHKSUM);
  writeString("stdout", *CHKSUM);
  writeLine("stdout", "    bagit.txt")
  msiDataObjChksum("*BAGITDATA" ++ "/manifest-md5.txt", "forceChksum", *CHKSUM);
  writeString("stdout", *CHKSUM);
  writeLine("stdout", "    manifest-md5.txt");
  msiDataObjCreate("*BAGITDATA" ++ "/tagmanifest-md5.txt", "destRescName=" ++ "*DESTRESC" ++ "++++forceFlag=", *FD);
  msiDataObjWrite(*FD, "stdout", *WLEN);
  msiDataObjClose(*FD, *Status);
  msiFreeBuffer("stdout");

  ### - writes to rodsLog
  msiWriteRodsLog("BagIt bag files created in place: *BAGITDATA <- *BAGITDATA", *Status);
}
INPUT *BAGITDATA="/dummy/dummy/dummy", *DESTRESC="dummy"
OUTPUT ruleExecOut
