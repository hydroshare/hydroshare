import { _Object, CommonPrefix, GetObjectCommand, ListObjectsV2Command, S3Client } from "@aws-sdk/client-s3";
import { Notifications } from "@cznethub/cznet-vue-core";
import { IFile, IFolder } from "@cznethub/cznet-vue-core/dist/types";

export const onFileDownload = async (items: (IFile | IFolder)[], resourceId: string, s3Client: S3Client, bucket: string) => {
  try {
    for (let item of items) {
      const basePrefix = `${resourceId}/data/contents/`;
      const key = `${basePrefix}${item.path}`;
      const result = await s3Client.send(
        new GetObjectCommand({ Bucket: bucket, Key: key }),
      );
      const blob = await result.Body?.transformToByteArray();
      if (blob) {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const a = document.createElement("a");
        a.href = url;
        a.download = key.split("/").pop() || "download";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    }
    Notifications.toast({
      title: "Success",
      message: "File downloaded successfully!",
      type: "success",
    });
  } catch (error: any) {
    console.error("Error downloading file:", error);
    Notifications.toast({
      title: "Error",
      message: `Failed to download file: ${error.message}`,
      type: "error",
    });
  }
}

export const readRootFolder = async (path: string, S3Client: S3Client, bucket: string): Promise<Partial<IFile | IFolder>[]> => {
  return _readFolderRecursive(path, S3Client, bucket);
}

export const _readFolderRecursive = async (
  path: string, s3Client: S3Client, bucket: string
): Promise<Partial<IFile | IFolder>[]> => {
  try {
    const command = new ListObjectsV2Command({
      Bucket: bucket,
      Prefix: path,
      Delimiter: "/",
    });
    const s3Response = await s3Client.send(command);

    let files: Partial<IFile>[] = [];
    let folders: Partial<IFolder>[] = [];

    // TODO: Parse out ignored files using new MIME type
    // FILES
    if (s3Response.Contents) {
      files = s3Response.Contents
        .filter(f => f.Key !== path)  // Filter out current directory file marker
        .map((f: _Object, _index: number) => {
          return {
            name: f.Key?.replace(path, ""),
            isUploaded: true,
            file: null,
            uploadedSize: f.Size,
            contentKey: f.Key
          };
        });
    }

    // FOLDERS
    if (s3Response.CommonPrefixes) {
      // ----------
      // TODO: trying to find MIME type
      // for (const prefixItem of s3Response.CommonPrefixes) {
      //   const folderKey = prefixItem.Prefix;
      //   if (!folderKey) continue;

      //   try {
      //     const checkCommand = new ListObjectsV2Command({
      //       Bucket: bucket,
      //       Prefix: folderKey,
      //     });
      //     const checkResult = await s3Client.send(checkCommand);
      //     console.log(checkResult)
      //   } catch (err) {
      //     console.warn(`Failed to verify folder contents for ${folderKey}:`, err);
      //   }
      // }
      // ---------

      folders = s3Response.CommonPrefixes.map(
        (p: CommonPrefix, _index: number) => {
          const folderKey = p.Prefix;
          const name = folderKey?.replace(path, "").replace(/\/$/, "");
          return {
            name: name,
            children: [],
            isUploaded: true,
          };
        },
      );
    }

    if (folders.length) {
      const readSubfolderPromises: Promise<Partial<IFile | IFolder>[]>[] =
        folders.map((f) => {
          return _readFolderRecursive(`${path}${f.name}/`, s3Client, bucket);
        });
      const responses = await Promise.all(readSubfolderPromises);

      folders.forEach((f, i) => {
        // @ts-expect-error Doesn't matter because we just need the initial structure to load the component. The keys will be generated then.
        f.children = responses[i] || [];
      });
    }

    return [...folders, ...files];
  } catch (e: any) {
    console.log(e);
  }

  return [];
}

export const fetchResource = async (resourceId: string, s3Client: S3Client, bucket: string, key: string) => {
  let data, initialStructure

  try {
    console.log(`Fetching metadata from S3: ${bucket}/${key}`);
    const result = await s3Client.send(
      new GetObjectCommand({ Bucket: bucket, Key: key }),
    );
    const bodyContents = await result.Body?.transformToString();

    try {
      data = JSON.parse(bodyContents || "");
      console.log(`Form data loaded from ${bucket}/${key}`);
    } catch (error) {
      console.warn("JSON parse failed, loading defaults:", error);
      return false
    }

    try {
      initialStructure = await readRootFolder(
        `${resourceId}/data/contents/`,
        s3Client,
        bucket,
      );
    } catch (e) {
      Notifications.toast({
        message: "Failed to load existing files.",
        type: "error",
        location: "top center",
      });
      return false
    }
    return { data, initialStructure }
  } catch (error) {
    console.error("S3 fetch failed:", error);
    // this.data = { ...this.defaults };
    Notifications.toast({
      title: "Error",
      message: "Failed to load metadata from S3.",
      type: "error",
    });
    return false
  }
}