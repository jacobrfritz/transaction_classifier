/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    // This helps avoid issues with worker threads in some Docker environments
    workerThreads: false,
    cpus: 1
  }
};

export default nextConfig;
