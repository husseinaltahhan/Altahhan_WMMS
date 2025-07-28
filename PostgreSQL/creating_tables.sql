CREATE TABLE topics (
	id SERIAL PRIMARY KEY,
	topic TEXT NOT NULL UNIQUE,
	date_created TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE esp32_boards (
	id SERIAL PRIMARY KEY,
	esp_name TEXT NOT NULL UNIQUE,
	date_installed TIMESTAMPTZ DEFAULT NOW(),
	board_location TEXT NOT NULL
);

CREATE TABLE messages (
	id SERIAL PRIMARY KEY,
	publishing_board INTEGER REFERENCES esp32_boards(id),
	message_topic INTEGER REFERENCES topics(id),
	payload TEXT NOT NULL,
	date_published TIMESTAMPTZ DEFAULT NOW(),
	UNIQUE (publishing_board, message_topic, payload, date_published)
);

CREATE TABLE production_log(
	id SERIAL PRIMARY KEY,
	board_id INTEGER REFERENCES esp32_boards(id),
	log_date DATE NOT NULL,
	cylinder_count INTEGER NOT NULL DEFAULT 0,
	UNIQUE(board_id, log_date)
);

CREATE TABLE subscriptions (
	id SERIAL PRIMARY KEY,
	board_id INTEGER REFERENCES esp32_boards(id) ON DELETE CASCADE,
	topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
	UNIQUE (board_id, topic_id)
);



