import pino from 'pino';

const isDev = process.env.NODE_ENV === 'development';

// Simple logger configuration that works well in Docker and avoids worker thread issues during build
const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: isDev ? {
    target: 'pino-pretty',
    options: {
      colorize: true
    }
  } : undefined,
});

export default logger;
