module.exports = {
  apps: [
    {
      name: "erp-backend",
      script: "/home/diva/amine_moussa/erp-ai-assistant/venv/bin/uvicorn",
      args: "backend.main:app --host 0.0.0.0 --port 8000",
      cwd: "/home/diva/amine_moussa/erp-ai-assistant",
      interpreter: "/home/diva/amine_moussa/erp-ai-assistant/venv/bin/python3",
      autorestart: true,
      watch: false,
      log_file: "/home/diva/amine_moussa/erp-ai-assistant/logs/backend.log",
      time: true,
      env: {
        PYTHONUNBUFFERED: "1",
        PYTHONPATH: "/home/diva/amine_moussa/erp-ai-assistant"
      }
    },
    {
      name: "erp-frontend",
      script: "/home/diva/amine_moussa/erp-ai-assistant/venv/bin/streamlit",
      args: "run /home/diva/amine_moussa/erp-ai-assistant/frontend/app.py --server.port 8501 --server.address 0.0.0.0",
      cwd: "/home/diva/amine_moussa/erp-ai-assistant",
      interpreter: "/home/diva/amine_moussa/erp-ai-assistant/venv/bin/python3",
      autorestart: true,
      watch: false,
      log_file: "/home/diva/amine_moussa/erp-ai-assistant/logs/frontend.log",
      time: true,
      env: {
        PYTHONUNBUFFERED: "1"
      }
    },
    {
      name: "erp-n8n",
      script: "n8n",
      args: "start",
      interpreter: "none",
      autorestart: true,
      watch: false,
      log_file: "/home/diva/amine_moussa/erp-ai-assistant/logs/n8n.log",
      time: true,
      env: {
        N8N_SECURE_COOKIE: "false"
      }
    }
  ]
};