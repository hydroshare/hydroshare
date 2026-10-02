import {
  S3Client,
  PutObjectCommand,
  DeleteObjectCommand,
} from "@aws-sdk/client-s3";
import { S3_PROXY_URL } from "@/constants";
import { isMarkdownFileName, toMarkdownFileName } from "./markdown";

// S3 access for the README editor, kept free of Vue. A README lives at
// `<resourceId>/data/contents/<name>`.

export function readmeKey(resourceId: string, name: string): string {
  return `${resourceId}/data/contents/${name}`;
}

function contentTypeFor(name: string): string {
  return isMarkdownFileName(name) ? "text/markdown" : "text/plain";
}

function byteLength(text: string): number {
  return new TextEncoder().encode(text).length;
}

/**
 * Fetch a README's raw text, bypassing caches so a reload after a save isn't
 * stale. `no-store` skips the HTTP cache; the unique query param defeats any
 * URL-keyed cache (e.g. the service worker). Cookie auth, no CSRF for GET.
 */
export async function loadReadme(
  bucket: string,
  resourceId: string,
  name: string,
): Promise<string> {
  const key = readmeKey(resourceId, name);
  const url = `${S3_PROXY_URL}/${bucket}/${key}?_=${Date.now()}`;
  const res = await fetch(url, { credentials: "include", cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Failed to read README (HTTP ${res.status})`);
  }
  return await res.text();
}

/** Overwrite the README in place. Returns the saved byte size. */
export async function saveReadme(
  s3Client: S3Client,
  bucket: string,
  resourceId: string,
  name: string,
  body: string,
): Promise<number> {
  await s3Client.send(
    new PutObjectCommand({
      Bucket: bucket,
      Key: readmeKey(resourceId, name),
      Body: body,
      ContentType: contentTypeFor(name),
    }),
  );
  return byteLength(body);
}

/** Write `<base>.md`, then delete the original `.txt`. */
export async function convertReadmeToMarkdown(
  s3Client: S3Client,
  bucket: string,
  resourceId: string,
  fromName: string,
  body: string,
): Promise<{ name: string; size: number }> {
  const toName = toMarkdownFileName(fromName);
  await s3Client.send(
    new PutObjectCommand({
      Bucket: bucket,
      Key: readmeKey(resourceId, toName),
      Body: body,
      ContentType: "text/markdown",
    }),
  );
  await s3Client.send(
    new DeleteObjectCommand({
      Bucket: bucket,
      Key: readmeKey(resourceId, fromName),
    }),
  );
  return { name: toName, size: byteLength(body) };
}
