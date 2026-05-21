/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { 
    unoptimized: true,
    domains: ['images.trvl-media.com'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'images.trvl-media.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
  webpack(config) {
    config.module.rules.push({
      test: /\.svg$/,
      use: ['@svgr/webpack'],
    });
    return config;
  },
  reactStrictMode: true,
  // experimental: {
  //   appDir: true,
  // },
};

module.exports = nextConfig;
