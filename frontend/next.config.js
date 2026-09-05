/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@dark-social/ui'],
  webpack(config) {
    config.resolve.alias['motion/react'] = require.resolve('motion/react');
    config.resolve.alias['lucide-react'] = require.resolve('lucide-react');
    config.resolve.alias.d3 = require.resolve('d3');
    return config;
  },
}

module.exports = nextConfig
