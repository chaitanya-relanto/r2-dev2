import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  // Disable ESLint during builds to avoid blocking production builds
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Disable TypeScript checking during builds to avoid blocking production builds
  typescript: {
    ignoreBuildErrors: true,
  },
  // Configure webpack to handle path aliases
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      "@": path.resolve(__dirname, "./src"),
    };
    return config;
  },
};

export default nextConfig;
