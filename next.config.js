/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    // バックエンドAPIのURLを環境変数から取得（Vercel環境変数に対応）
    const backendUrl = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;