/*
 * ESP32Cam-OV2640Camera  Wi-Fi Web Server for MJPEG Video Streaming & Multi-Resolution Still Capture 
 * 
 * Copyright (c) 2025 Dr.K.K.Thyagharajan, Professor & Dean (Research), RMD Engineering College, Kavaraipettai
 * 
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the MIT License. For a full copy of the license,
 * see the LICENSE file in the project's root directory.
 * 
 * This program relies on the esp32cam library by yoursunny,
 * which is licensed under the ISC License.
 */
// ************************************************************
// USER CONFIGURATION: SETUP INSTRUCTIONS
// ************************************************************
// 1. Fill in your Wi-Fi credentials below.
// 2. Ensure you have the 'esp32cam' library by yoursunny installed.
// 3. Select the correct board (AI Thinker ESP32-CAM) and port in the IDE.
// 4. Connect the ESP32-CAM to a stable power source (5V recommended).
// ************************************************************
// WARNING: Never commit your actual password to a public repository!
// ************************************************************

#include <WebServer.h>
#include <WiFi.h>
#include <esp32cam.h>
 
const char* WIFI_SSID = ""; //Include your Wi-FI's SSID and Password
const char* WIFI_PASS = "";

 
WebServer server(80);
 
 
static auto loRes = esp32cam::Resolution::find(320, 240);
static auto midRes = esp32cam::Resolution::find(640, 480);
static auto hiRes = esp32cam::Resolution::find(800, 600);
void serveJpg()
{
  auto frame = esp32cam::capture();
  if (frame == nullptr) {
    Serial.println("CAPTURE FAIL");
    server.send(503, "", "");
    return;
  }
  Serial.printf("CAPTURE OK %dx%d %db\n", frame->getWidth(), frame->getHeight(),
                static_cast<int>(frame->size()));
 
  server.setContentLength(frame->size());
  server.send(200, "image/jpeg");
  WiFiClient client = server.client();
  frame->writeTo(client);
}
 
void handleJpgLo()
{
  if (!esp32cam::Camera.changeResolution(loRes)) {
    Serial.println("SET-LO-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgHi()
{
  if (!esp32cam::Camera.changeResolution(hiRes)) {
    Serial.println("SET-HI-RES FAIL");
  }
  serveJpg();
}
 
void handleJpgMid()
{
  if (!esp32cam::Camera.changeResolution(midRes)) {
    Serial.println("SET-MID-RES FAIL");
  }
  serveJpg();
}
 
 
void  setup(){
  Serial.begin(115200);
  Serial.println();
  {
    using namespace esp32cam;
    Config cfg;
    cfg.setPins(pins::AiThinker);
    cfg.setResolution(loRes); // QVGA 320x240
    //cfg.setResolution(midRes); // QVGA 640x480
    //cfg.setResolution(hiRes);  //800x600
    cfg.setBufferCount(1); // 1 or 2
    cfg.setJpeg(70);  //reduce quality from 80 to 70 
 
    bool ok = Camera.begin(cfg);
    Serial.println(ok ? "CAMERA OK" : "CAMERA FAIL");
  }
  WiFi.persistent(false);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
  Serial.print("http://");
  Serial.println(WiFi.localIP());
  Serial.println("  /cam-lo.jpg");
  Serial.println("  /cam-hi.jpg");
  Serial.println("  /cam-mid.jpg");

  //For capturing a frame
  server.on("/cam-lo.jpg", handleJpgLo);
  server.on("/cam-hi.jpg", handleJpgHi);
  server.on("/cam-mid.jpg", handleJpgMid);

  //For streaming the video
  server.on("/stream", []() {
  WiFiClient client = server.client();

  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
  server.sendContent(response);

  unsigned long lastFrameTime = millis();

  while (client.connected()) {
    auto frame = esp32cam::capture();
    if (!frame) {
      Serial.println("Capture failed");
      delay(100);
      continue;
    }

    server.sendContent("--frame\r\n");
    server.sendContent("Content-Type: image/jpeg\r\n\r\n");
    client.write(frame->data(), frame->size());
    server.sendContent("\r\n");

    delay(100); // 10 FPS
    
    // Optional safety: break if stuck too long
    if (millis() - lastFrameTime > 5000) {
      Serial.println("Stream timeout, breaking...");
      break;
    }

    lastFrameTime = millis(); // reset timer
  }

  Serial.println("Client disconnected or stream ended");
});


  server.begin();
}
 
void loop()
{
  server.handleClient();
}
