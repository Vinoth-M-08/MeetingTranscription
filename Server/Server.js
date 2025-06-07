require('dotenv').config({ path: './Common.env' });
const http = require("http");
const { WebSocketServer } = require("ws");
const WebSocket = require("ws");

const server = http.createServer();
const wsServer = new WebSocketServer({ server });
const port = 8000;
let pythonSocket;

// Connect to Python Service
function connectToPython() {
  pythonSocket = new WebSocket("ws://localhost:5001");

  pythonSocket.on("open", () => console.log("Connected to Python service."));

  pythonSocket.on("close", (code, reason) => {
    console.warn(`Python socket closed (Code: ${code}, Reason: ${reason}). Reconnecting in 3 seconds...`);
    setTimeout(connectToPython, 3000);
  });

  pythonSocket.on("error", (error) => console.error("Python Socket Error:", error));

  pythonSocket.on("message", (response) => {
    console.log("Received from Python:", response.toString());
    wsServer.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(response.toString());
      }
    });
  });
}
connectToPython();

// Handle Client Connection
wsServer.on("connection", (clientWs) => {
  console.log("Client connected");

  clientWs.on("message", async (data) => {
    try {
      const { action, fileName, audioData, speakerName } = JSON.parse(data);
      console.log(`Received action: ${action}`);

      switch (action) {
        case "identify":
          handleIdentify(clientWs, { fileName, audioData });
          break;

        case "extract":
          if (!speakerName) {
            clientWs.send(JSON.stringify({ error: "Speaker name is required for extraction" }));
          } else if (audioData) {
            handleAudioProcessing(clientWs, { action, fileName, audioData, speakerName });
          }
          break;

        case "diarize":
          handleDiarize(clientWs, { fileName, audioData });
          break;
        case "view_embeddings":
          handleViewEmbeddings(clientWs); 
          break;
        default:
          clientWs.send(JSON.stringify({ error: "Invalid action" }));
      }
    } catch (error) {
      console.error("Error processing request:", error);
      clientWs.send(JSON.stringify({ error: "An error occurred" }));
    }
  });

  clientWs.on("close", () => console.log("Client disconnected"));
});

// Handle Speaker Identification
function handleIdentify(clientWs, { fileName, audioData }) {
  if (pythonSocket.readyState === WebSocket.OPEN) {
    console.log("Sending identification request to Python service...");
    pythonSocket.send(JSON.stringify({ action: "identify", fileName, audioData }));
  } else {
    console.error("Python service is not connected.");
    clientWs.send(JSON.stringify({ error: "Python service not available" }));
  }
}

// Handle Viewing Embeddings
function handleViewEmbeddings(clientWs) {
  if (pythonSocket.readyState === WebSocket.OPEN) {
    console.log("Requesting embeddings from Python service...");
    pythonSocket.send(JSON.stringify({ action: "view_embeddings" }));
  } else {
    console.error("Python service is not connected.");
    clientWs.send(JSON.stringify({ error: "Python service not available" }));
  }
}

// Handle Audio Processing
function handleAudioProcessing(clientWs, { action, fileName, audioData, speakerName }) {
  if (pythonSocket.readyState === WebSocket.OPEN) {
    console.log("Connected to Python service for audio processing");
    pythonSocket.send(JSON.stringify({ action, fileName, audioData, speakerName }));
  } else {
    console.error("Python service is not connected.");
    clientWs.send(JSON.stringify({ error: "Python service not available" }));
  }
}

// Handle Diarization
function handleDiarize(clientWs, { fileName, audioData }) {
  if (pythonSocket.readyState === WebSocket.OPEN) {
    console.log("Sending diarization request to Python service...");
    pythonSocket.send(JSON.stringify({ action: "diarize", fileName, audioData }));
  } else {
    console.error("Python service is not connected.");
    clientWs.send(JSON.stringify({ error: "Python service not available" }));
  }
}

server.listen(port, () => {
  console.log(`Node.js WebSocket server started on port ${port}`);
});
