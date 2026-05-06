#pragma once
#include <Arduino.h>
#include <WebSocketsClient.h>
#include "../led/led_manager.h"
#include "../protocol/message_types.h"

class EeWebSocketClient {
public:
    EeWebSocketClient();
    void begin(const char* host, uint16_t port, const char* deviceId, LedManager* ledManager);
    void loop();
    bool isConnected() const;
    void sendRegister(const char* firmwareVersion, const char* boardTarget);
    void sendHeartbeat(unsigned long timestampMs);
    void sendEvent(const EventPayload& payload, bool testEvent = false);

private:
    WebSocketsClient _client;
    String _deviceId;
    const char* _firmwareVersion = "unknown";
    const char* _boardTarget = "unknown";
    LedManager* _ledManager = nullptr;
    bool _connected = false;

    void handleEvent(WStype_t type, uint8_t* payload, size_t length);
    void applyTransition(const StateTransitionPayload& transition);
};
