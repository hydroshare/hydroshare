/** S3 key for an uploaded file. Segments stay unencoded; the request layer encodes them. */
export function buildUploadKey(
  basePrefix: string,
  folderPath: string | null | undefined,
  fileName: string,
): string {
  const folder = (folderPath || "").replace(/^\/+|\/+$/g, "");
  return `${basePrefix}${folder ? `${folder}/` : ""}${fileName}`;
}
