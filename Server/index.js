  const http = require("http");
  const { WebSocketServer } = require("ws");
  const { exec } = require("child_process");
  const fs = require("fs");

  const server = http.createServer();
  const wsServer = new WebSocketServer({ server });

  const port = 8000;

  // WebSocket Connection
  wsServer.on("connection", (ws) => {
    console.log("Client connected");

    ws.on("message", (data) => {
      try {
        const receivedData = JSON.parse(data);
        
        if (receivedData.type === "audio_upload") {
          console.log("Audio received for processing...");

          // Save audio to a file
          const audioBuffer = Buffer.from(receivedData.audioData, "base64");
          const audioPath = `audio_input.wav`;
          fs.writeFileSync(audioPath, audioBuffer);

          console.log("Audio saved successfully!");

          // Execute Python script
          exec(`python3 identify.py ${audioPath}`, (error, stdout, stderr) => {
            if (error) {
              console.error(`Error: ${error.message}`);
              ws.send(JSON.stringify({ type: "error", message: error.message }));
              return;
            }
            if (stderr) console.error(`stderr: ${stderr}`);

            console.log("Python Output:", stdout);
            ws.send(JSON.stringify({ type: "result", message: stdout.trim() }));
          });
        }
      } catch (err) {
        console.error("Error processing message:", err.message);
      }
    });

    ws.on("close", () => console.log("Client disconnected"));
  });

  server.listen(port, () => {
    console.log(`Server running on port ${port}`);
  });
