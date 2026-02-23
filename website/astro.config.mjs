import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";

export default defineConfig({
  site: "https://hikaruegashira.github.io",
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
        { label: "Introduction", slug: "introduction" },
        { label: "Specification v0.1", slug: "spec" },
        {
          label: "SDKs",
          items: [
            { label: "Python", slug: "sdk-python" },
            { label: "TypeScript", slug: "sdk-typescript" },
          ],
        },
      ],
    }),
  ],
});
