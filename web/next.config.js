/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: { unoptimized: true },
  // The pipeline writes editions as static JSON to public/editions/. Next.js
  // does NOT bundle public/ into serverless functions by default, so we trace
  // those files into the routes that read them at runtime (for ISR/new dates).
  // The current edition is also statically pre-rendered via generateStaticParams,
  // so the site works even if this trace is ignored on older Next versions.
  experimental: {
    outputFileTracingIncludes: {
      "/": ["./public/editions/**"],
      "/edition/[date]": ["./public/editions/**"],
      "/all-news/[date]": ["./public/editions/**"],
    },
  },
};
module.exports = nextConfig;
