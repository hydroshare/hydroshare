/** Upload limits for a resource. `remainingQuota` is `null` when quota is not enforced. */
export interface UploadLimits {
  maxFileSize: number;
  maxNumberOfFiles: number;
  remainingQuota: number | null;
}

export const DEFAULT_UPLOAD_LIMITS: UploadLimits = {
  maxFileSize: 25 * 1024 ** 3,
  maxNumberOfFiles: 50,
  remainingQuota: null,
};

/** Static limits the landing page view exposes on the host window as `HS_UPLOAD_LIMITS`. */
export function hostUploadLimits(host: unknown): UploadLimits {
  let raw: any;
  try {
    raw = (host as any)?.HS_UPLOAD_LIMITS;
  } catch {
    // cross-origin host
  }
  return {
    ...DEFAULT_UPLOAD_LIMITS,
    maxFileSize: Number(raw?.maxFileSize) || DEFAULT_UPLOAD_LIMITS.maxFileSize,
    maxNumberOfFiles:
      Number(raw?.maxNumberOfFiles) || DEFAULT_UPLOAD_LIMITS.maxNumberOfFiles,
  };
}

/** Remaining quota of the resource's quota holder, or `null` when quota is not enforced. */
export async function fetchRemainingQuota(
  resourceId: string,
): Promise<number | null> {
  const response = await fetch(`/hsapi/_internal/${resourceId}/remaining-quota/`, {
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Failed to load remaining quota (${response.status}).`);
  }
  const data = await response.json();
  return data.remaining_quota === null || data.remaining_quota === undefined
    ? null
    : Math.max(Number(data.remaining_quota) || 0, 0);
}

/** Formats bytes the way Django's `filesizeformat` does (1024 based, one decimal). */
export function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} ${bytes === 1 ? "byte" : "bytes"}`;
  }
  const units = ["KB", "MB", "GB", "TB", "PB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit++;
  }
  return `${value.toFixed(1)} ${units[unit]}`;
}

/** Remaining quota after this session's uploads, or `null` when quota is not enforced. */
export function availableQuota(
  limits: UploadLimits,
  uploadedBytes: number,
): number | null {
  if (limits.remainingQuota === null) {
    return null;
  }
  return Math.max(limits.remainingQuota - uploadedBytes, 0);
}

/** Largest single file that can be uploaded right now. */
export function maxUploadSize(limits: UploadLimits, quota: number | null) {
  return quota === null ? limits.maxFileSize : Math.min(limits.maxFileSize, quota);
}

export function uploadHelpText(limits: UploadLimits, quota: number | null) {
  if (quota !== null && quota <= 0) {
    return "Uploads are disabled because the quota holder of this resource has no remaining quota.";
  }
  const sizeText = `Upload files up to ${formatFileSize(limits.maxFileSize)} in size by dragging & dropping.`;
  return quota === null
    ? sizeText
    : `${sizeText} Remaining quota: ${formatFileSize(quota)}.`;
}

/** Returns why a batch of files cannot be uploaded, or `null` if it can. */
export function quotaError(
  sizes: number[],
  limits: UploadLimits,
  quota: number | null,
): string | null {
  const maxSize = maxUploadSize(limits, quota);
  const tooLarge = sizes.find((size) => size > maxSize);
  if (tooLarge !== undefined) {
    return quota !== null && quota < limits.maxFileSize
      ? `A file of ${formatFileSize(tooLarge)} exceeds the remaining quota of ${formatFileSize(quota)}.`
      : `Files cannot be larger than ${formatFileSize(limits.maxFileSize)}.`;
  }
  if (quota !== null) {
    const total = sizes.reduce((acc, size) => acc + size, 0);
    if (total > quota) {
      return `The selected files (${formatFileSize(total)}) exceed the remaining quota of ${formatFileSize(quota)}.`;
    }
  }
  return null;
}
