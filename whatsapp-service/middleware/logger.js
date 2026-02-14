// middleware/logger.js
const logger = (req, res, next) => {
  const timestamp = new Date().toISOString();
  const { method, url } = req;

  // Log when the request starts
  console.log(`[${timestamp}] ${method} ${url}`);

  // Optional: Log when the request finishes to see the status code
  res.on("finish", () => {
    console.log(`[${timestamp}] ${method} ${url} - Status: ${res.statusCode}`);
  });

  next(); // Move to the next middleware/route
};

module.exports = logger;
