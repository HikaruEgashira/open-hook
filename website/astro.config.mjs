import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://plenoai.com",
  base: "/open-hook",
  integrations: [
    starlight({
      title: "OpenHook",
      description:
        "A lightweight protocol that standardizes hook payloads for AI coding agent tools.",
      social: {
        github: "https://github.com/HikaruEgashira/open-hook",
      },
      sidebar: [
        { label: "Introduction", autogenerate: { directory: "." } },
        {
          label: "SDKs",
          autogenerate: { directory: "sdks" },
        },
      ],
    }),
  ],
});
