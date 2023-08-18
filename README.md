# Nexus

Nexus is a privacy-first, open-source AI-powered personal assistant infrastructure designed to facilitate communication, user interaction, and task execution across various channels.

## Concept

Nexus is a collection of distributed microservices communicating through an internal API. Its primary goal is to receive messages from multiple sources (e.g., Telegram, Discord, etc.), identify users, process input, determine the appropriate task to perform, initiate the corresponding routine, and provide responses.

## Modules
1. comms
The `comms` module manages the receipt and sending of messages via the relevant communication channels.
2. core
The `core` module serves as the high-level logic of the system, interpreting user requests, making task decisions, and performing other functions.
3. taskmanager
The `taskmanager` module is responsible for receiving tasks from the core, initiating, monitoring their progress, and providing the necessary data back to the user.
4. transcriber
The `transcriber` module utilizes AI to perform audio-to-text transcription.
5. synthesizer
The `synthesizer` module converts text into speech to deliver audio responses to users.

## Getting Started

1. Clone the repository: git clone [repository_url]
2. Install the required dependencies: pip install -r requirements.txt
3. Configure environment variables:
`TELEGRAM_API_ID`: Your Telegram API ID
`TELEGRAM_API_HASH`: Your Telegram API hash
`TELEGRAM_API_TOKEN`: Your Telegram bot token
`CORE_PORT`: Port for the core module
`MANAGER_PORT`: Port for the task manager module
`COMMS_PORT`: Port for the communication module
4. Start the individual modules:
Run `comms.py` to start the communication module.
Run `core.py` to start the core module.
Run `taskmanager.py` to start the task manager module.

## Usage

Once Nexus is up and running, you can interact with it through the supported communication channels (e.g., Telegram) to initiate various tasks and receive responses.

1. Sending Messages
To send a message to Nexus, you can use the provided API endpoints. For example, you can use the `/api/message_to_user` endpoint to send a message from a user to Nexus.
```POST /api/message_to_user
Content-Type: application/json

{
  "user": {
    "name": "username",
    "id": "user_id"
  },
  "chat": "chat_id",
  "channel": "telegram",
  "text": "Hello, Nexus!"
}```

2. Running Tasks
Nexus supports various tasks that can be executed through the `/api/run_task` endpoint. You can provide the necessary parameters and options to specify the task you want to perform.
```POST /api/run_task
Content-Type: application/json

{
  "name": "task_name",
  "parameter": "task_parameter",
  "options": {
    "option_name": "option_value"
  }
}```