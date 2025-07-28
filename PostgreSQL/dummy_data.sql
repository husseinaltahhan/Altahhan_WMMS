-- Insert a topic
INSERT INTO topics (topic) VALUES ('factory/machine1/status');

-- Insert a board
INSERT INTO esp32_boards (esp_name, board_location) 
VALUES ('esp32_001', 'Assembly Line A');

-- Subscribe the board to the topic
INSERT INTO subscriptions (board_id, topic_id)
VALUES (
  (SELECT id FROM esp32_boards WHERE esp_name = 'esp32_001'),
  (SELECT id FROM topics WHERE topic = 'factory/machine1/status')
);

-- Log a message
INSERT INTO messages (publishing_board, message_topic, payload)
VALUES (
  (SELECT id FROM esp32_boards WHERE esp_name = 'esp32_001'),
  (SELECT id FROM topics WHERE topic = 'factory/machine1/status'),
  'Machine is online'
);




