import { trackHostViewport } from "@/util/host-viewport";
import type { UserModule } from "@/types";

export const install: UserModule = ({ isClient }) => {
  if (isClient) trackHostViewport();
};
