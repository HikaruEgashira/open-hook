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
      social: [
        {
          icon: "github",
          label: "GitHub",
          href: "https://github.com/HikaruEgashira/open-hook",
        },
      ],
      sidebar: [
        {
          label: "Introduction",
          items: [{ autogenerate: { directory: "." } }],
        },
        {
          label: "SDKs",
          items: [{ autogenerate: { directory: "sdks" } }],
        },
      ],
    }),
  ],
});
