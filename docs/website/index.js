import express from 'express';
import path from 'path';

const app = express();
const PORT = 4000;

// Resolve the __dirname path (ESM doesn't have __dirname by default)
const __dirname = path.resolve();

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Handle the root path and serve index.html
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
