# 🎧 Global Radio Discord Bot

This Discord bot allows you to listen to any radio station from around the world directly in your Discord voice channel. Powered by Docker for easy setup.

## ✨ Features

- **Global Radio Access**: Connects to a vast number of online radio streams.
- **Slash Commands**: Easy-to-use commands for controlling the bot.
- **Easy Deployment**: Get your bot running quickly with Docker Compose.

## 🚀 Getting Started

Follow these simple steps to get your own Global Radio Discord Bot up and running.

### Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Git**: For cloning the repository.
- **Docker**: Docker Engine and Docker Compose (usually included with Docker Desktop).

### Setup Instructions

#### 1. Clone the Repository

Open your terminal or command prompt and clone this repository to your local machine:

```bash
git clone https://github.com/helish88/discord_radio_bot.git
```

#### 2. Navigate to the Project Directory

Change your current directory to the newly cloned project folder:

```bash
cd discord_radio_bot
```

#### 3. Create Your Environment File (.env)

This file will store your Discord bot token securely. It's crucial that this file is NOT committed to your Git repository.

Create a new file named `.env` in the root directory of the project (the same directory where `docker-compose.yml` is located).

**On Linux/macOS:**
```bash
touch .env
```

**On Windows (PowerShell):**
```powershell
New-Item -Path ".\.env" -ItemType "File"
```

Open the newly created `.env` file with a text editor and add the following line:

```env
BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE
```

> **Important**: Replace `YOUR_DISCORD_BOT_TOKEN_HERE` with your actual Discord bot token obtained from the [Discord Developer Portal](https://discord.com/developers/applications). Remember to keep your token confidential!

#### 4. Run the Bot with Docker Compose

Once your `.env` file is set up, you can start the bot using Docker Compose. This command will build the Docker image (if not already built) and run the bot in the background.

```bash
sudo docker-compose up --build -d
```

**Command explanation:**
- `sudo`: May be required on Linux systems for Docker commands.
- `up`: Starts the services defined in docker-compose.yml.
- `--build`: Forces Docker to re-build the image(s) before starting, ensuring you have the latest code.
- `-d`: Runs the services in "detached" mode, meaning they run in the background, and your terminal will be free.

## 🛑 Stopping the Bot

To stop the bot and remove the running Docker containers, use:

```bash
sudo docker-compose down
```

## 🤝 Contributing

Feel free to fork the repository, make improvements, and submit pull requests.

## 📧 Support & Feedback

[SOON ))]
