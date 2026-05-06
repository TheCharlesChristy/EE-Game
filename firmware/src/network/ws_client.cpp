#include "ws_client.h"
#include "../protocol/message_codec.h"

EeWebSocketClient::EeWebSocketClient() {}

void EeWebSocketClient::begin(const char* host, uint16_t port, const char* deviceId, LedManager* ledManager) {
    _deviceId = deviceId;
    _ledManager = ledManager;
    String path = "/ws/devices/" + _deviceId;
    _client.begin(host, port, path.c_str());
    _client.onEvent([this](WStype_t type, uint8_t* payload, size_t length) {
        this->handleEvent(type, payload, length);
    });
    _client.setReconnectInterval(3000);
}

void EeWebSocketClient::loop() {
    _client.loop();
}

bool EeWebSocketClient::isConnected() const {
    return _connected;
}

void EeWebSocketClient::sendRegister(const char* firmwareVersion, const char* boardTarget) {
    _firmwareVersion = firmwareVersion;
    _boardTarget = boardTarget;
    if (!_connected) return;
    String message = MessageCodec::encodeRegister(_deviceId.c_str(), _firmwareVersion, _boardTarget);
    _client.sendTXT(message);
}

void EeWebSocketClient::sendHeartbeat(unsigned long timestampMs) {
    if (!_connected) return;
    String message = MessageCodec::encodeHeartbeat(_deviceId.c_str(), timestampMs);
    _client.sendTXT(message);
}

void EeWebSocketClient::sendEvent(const EventPayload& payload, bool testEvent) {
    if (!_connected) return;
    String message = MessageCodec::encodeEvent(_deviceId.c_str(), payload, testEvent);
    _client.sendTXT(message);
}

void EeWebSocketClient::handleEvent(WStype_t type, uint8_t* payload, size_t length) {
    switch (type) {
        case WStype_CONNECTED:
            _connected = true;
            if (_ledManager) _ledManager->setState(LedState::CONNECTED);
            sendRegister(_firmwareVersion, _boardTarget);
            break;
        case WStype_DISCONNECTED:
            _connected = false;
            if (_ledManager) _ledManager->setState(LedState::CONNECTING);
            break;
        case WStype_TEXT: {
            String text;
            text.reserve(length + 1);
            for (size_t i = 0; i < length; i++) text += static_cast<char>(payload[i]);
            StateTransitionPayload transition;
            if (MessageCodec::decodeStateTransition(text, transition)) {
                applyTransition(transition);
            }
            break;
        }
        default:
            break;
    }
}

void EeWebSocketClient::applyTransition(const StateTransitionPayload& transition) {
    if (!_ledManager) return;
    if (transition.led_state == "live") {
        _ledManager->setState(LedState::LIVE);
    } else if (transition.led_state == "test_fault") {
        _ledManager->setState(LedState::TEST_FAULT);
    } else if (transition.led_state == "connecting") {
        _ledManager->setState(LedState::CONNECTING);
    } else {
        _ledManager->setState(LedState::CONNECTED);
    }
}
