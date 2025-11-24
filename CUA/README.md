# CUA - Computer Use Agent 2.0

An AI-powered browser automation service that enables automated appointment scheduling and other web-based tasks. This service is integrated into the main platform to provide intelligent scheduling capabilities via Calendly and other platforms.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Hugging Face account with API token
- E2B account with API key

### Running CUA

1. **Navigate to the CUA directory:**
   ```bash
   cd CUA
   ```

2. **Export required environment variables:**
   ```bash
   export HF_TOKEN=your_huggingface_token
   export E2B_API_KEY=your_e2b_api_key
   ```

3. **Build the Docker image:**
   ```bash
   make docker-build
   ```

4. **Run the CUA service:**
   ```bash
   make docker-run
   ```

5. **Access CUA:**
   - Web Interface: http://localhost:7860
   - WebSocket: ws://localhost:7860/ws

### Managing CUA

```bash
# View logs
make docker-logs

# Stop the service
make docker-stop

# Clean up Docker images
make docker-clean
```

## 🔧 Configuration

### Environment Variables

CUA requires the following environment variables:

- **HF_TOKEN** (required): Your Hugging Face API token for model inference
  - Get it from: https://huggingface.co/settings/tokens
  - Used for AI model inference during browser automation

- **E2B_API_KEY** (required): Your E2B API key for sandbox environments
  - Get it from: https://e2b.dev/dashboard
  - Used for isolated browser sandbox execution

### Integration with Main Platform

The main platform connects to CUA via:
- **WebSocket URL**: `ws://localhost:7860/ws` (configurable via `CUA_WS_URL` env var)
- **HTTP URL**: `http://localhost:7860` (for health checks and frontend iframe)

## 📋 Available Make Commands

- `make docker-build` - Build the Docker image
- `make docker-run` - Run the CUA container (requires HF_TOKEN and E2B_API_KEY)
- `make docker-stop` - Stop and remove the running container
- `make docker-clean` - Remove Docker images
- `make docker-logs` - View container logs (follow mode)
- `make sync` - Sync all dependencies (Python + Node.js)
- `make test` - Run tests
- `make clean` - Clean build artifacts

## 🏗️ Architecture

CUA consists of two main components:

1. **cua2-core** (Backend)
   - FastAPI server with WebSocket support
   - Browser automation engine
   - AI agent orchestration
   - Task execution and monitoring

2. **cua2-front** (Frontend)
   - React + TypeScript interface
   - Real-time task visualization
   - Step-by-step execution display
   - Screenshot and trace viewing

## 🔌 Integration Details

### How It Works

1. **User requests appointment** via the public chat interface
2. **Chat agent** (LangChain) collects scheduling details (name, email, date, time)
3. **Scheduling tool** sends task to CUA via WebSocket
4. **CUA agent** automates browser to schedule on Calendly
5. **Results** are streamed back to the chat interface
6. **User receives** confirmation or error message

### WebSocket Protocol

CUA uses a WebSocket protocol for task communication:

1. **Connection**: Client connects to `ws://localhost:7860/ws`
2. **Heartbeat**: CUA sends initial heartbeat with `trace_id` (UUID)
3. **Task Submission**: Client sends task with the received `trace_id`
4. **Progress Updates**: CUA streams `agent_progress` events with steps
5. **Completion**: CUA sends `agent_complete` event with final state
6. **Final Answer**: Agent's final answer is extracted from step actions

### Key Features

- **Real-time Progress**: Live updates during task execution
- **Visual Feedback**: Screenshots and step-by-step visualization
- **Error Handling**: Graceful failure detection and reporting
- **Final Answer Extraction**: Captures agent's explanation of results
- **Timeout Protection**: Configurable timeouts for long-running tasks

## 🐛 Troubleshooting

### Container won't start

- Ensure `HF_TOKEN` and `E2B_API_KEY` are exported
- Check Docker is running: `docker ps`
- View logs: `make docker-logs`

### Connection errors

- Verify CUA is running: `curl http://localhost:7860/health`
- Check WebSocket URL in backend config: `CUA_WS_URL=ws://localhost:7860/ws`
- Ensure firewall allows connections on port 7860

### Task execution fails

- Check Hugging Face token has sufficient permissions
- Verify E2B API key is valid and has credits
- Review logs for specific error messages: `make docker-logs`

## 📝 Notes

- CUA is integrated directly into the main repository (not a git submodule)
- The `get_model.py` file has been modified to remove `bill_to="smolagents"` parameter
- This allows billing to your personal Hugging Face account
- CUA runs in a Docker container for isolation and consistency

## 🔗 Related Documentation

- [Main Platform README](../README.md) - Full platform documentation
- [CUA Makefile](Makefile) - Available commands and build process
- [Backend Integration](../backend/app/services/cua_client.py) - WebSocket client implementation
- [Scheduling Tool](../backend/app/services/cua_scheduling_tool.py) - Appointment scheduling integration
