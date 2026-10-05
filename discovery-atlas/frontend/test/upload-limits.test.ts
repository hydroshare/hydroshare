import { describe, it, expect } from "vitest";
import {
  availableQuota,
  formatFileSize,
  maxUploadSize,
  quotaError,
  uploadHelpText,
  type UploadLimits,
} from "@/components/landing-page/upload-limits";

const GB = 1024 ** 3;
const limits = (remainingQuota: number | null): UploadLimits => ({
  maxFileSize: 25 * GB,
  maxNumberOfFiles: 50,
  remainingQuota,
});

describe("formatFileSize", () => {
  it("matches Django's filesizeformat", () => {
    expect(formatFileSize(1)).toBe("1 byte");
    expect(formatFileSize(512)).toBe("512 bytes");
    expect(formatFileSize(1536)).toBe("1.5 KB");
    expect(formatFileSize(25 * GB)).toBe("25.0 GB");
    expect(formatFileSize(2048 * GB)).toBe("2.0 TB");
  });
});

describe("availableQuota", () => {
  it("is null when quota is not enforced", () => {
    expect(availableQuota(limits(null), 5 * GB)).toBeNull();
  });

  it("subtracts bytes uploaded in this session and never goes negative", () => {
    expect(availableQuota(limits(20 * GB), 5 * GB)).toBe(15 * GB);
    expect(availableQuota(limits(1 * GB), 5 * GB)).toBe(0);
  });
});

describe("maxUploadSize", () => {
  it("is the smaller of the file size limit and the remaining quota", () => {
    expect(maxUploadSize(limits(null), null)).toBe(25 * GB);
    expect(maxUploadSize(limits(30 * GB), 30 * GB)).toBe(25 * GB);
    expect(maxUploadSize(limits(2 * GB), 2 * GB)).toBe(2 * GB);
  });
});

describe("uploadHelpText", () => {
  it("shows the size limit and the remaining quota", () => {
    expect(uploadHelpText(limits(20 * GB), 20 * GB)).toBe(
      "Upload files up to 25.0 GB in size by dragging & dropping. Remaining quota: 20.0 GB.",
    );
  });

  it("omits the quota when it is not enforced", () => {
    expect(uploadHelpText(limits(null), null)).toBe(
      "Upload files up to 25.0 GB in size by dragging & dropping.",
    );
  });

  it("explains that uploads are disabled when the quota is used up", () => {
    expect(uploadHelpText(limits(0), 0)).toMatch(/Uploads are disabled/);
  });
});

describe("quotaError", () => {
  it("accepts files within the limits", () => {
    expect(quotaError([GB, GB], limits(20 * GB), 20 * GB)).toBeNull();
    expect(quotaError([10 * GB], limits(null), null)).toBeNull();
  });

  it("rejects a file over the per-file limit", () => {
    expect(quotaError([26 * GB], limits(null), null)).toMatch(
      /cannot be larger than 25.0 GB/,
    );
  });

  it("rejects a file over the remaining quota", () => {
    expect(quotaError([3 * GB], limits(2 * GB), 2 * GB)).toMatch(
      /remaining quota of 2.0 GB/,
    );
  });

  it("rejects a batch whose total exceeds the remaining quota", () => {
    expect(quotaError([2 * GB, 2 * GB], limits(3 * GB), 3 * GB)).toMatch(
      /4.0 GB.*remaining quota of 3.0 GB/,
    );
  });
});
