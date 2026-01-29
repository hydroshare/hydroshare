import timeago from "vue-timeago3";
import type { UserModule } from "@/types";

export const install: UserModule = ({ app }) => {
  app.use(timeago);
};
