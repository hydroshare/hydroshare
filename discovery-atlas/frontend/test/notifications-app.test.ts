import { describe, it, expect, vi } from "vitest";
import { getNotificationsApp } from "@/components/landing-page/notifications-app";

describe("getNotificationsApp", () => {
  it("returns null when no notification app is present", () => {
    expect(getNotificationsApp()).toBeNull();
  });

  it("ignores a global that lacks registerTask", () => {
    vi.stubGlobal("notificationsApp", { show: () => {} });
    expect(getNotificationsApp()).toBeNull();
    vi.unstubAllGlobals();
  });
});
