/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: true,
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback.fs = false;
    }

    return config;
  },
  // Proxy API requests to FastAPI server during development to avoid CORS issues.
  // This requires some care to handle trailing slashes correctly, see:
  // https://github.com/vercel/next.js/discussions/36219#discussioncomment-4167863
  trailingSlash: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8935/api/:path*'
      },
      {
        source: '/api/:path*/',
        destination: 'http://localhost:8935/api/:path*/'
      }
    ]
  }
};
