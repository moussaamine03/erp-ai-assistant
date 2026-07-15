module.exports = {
  apps: [
    {
      // ------------------------------------------------------------
      // VUES (Achat, Article, Facturation, Facturation détail article)
      // Reconstruites une seule fois à chaque lancement du projet.
      // autorestart:false => tourne une fois, se termine, PM2 ne
      // relance pas automatiquement (sauf "pm2 restart" manuel).
      // ------------------------------------------------------------
      name: "views-startup",
      script: "run_sql.js",
      args: "sql/views_startup.sql",
      cwd: "/home/diva/amine_moussa/erp-ai-assistant/db-automation",
      interpreter: "node",
      autorestart: false,
      watch: false,
      log_file: "/home/diva/amine_moussa/erp-ai-assistant/logs/views-startup.log",
      time: true
    },
    {
      // ------------------------------------------------------------
      // TABLES RH_PRODUCTION
      // Rafraîchies tous les jours à 02:00. cron_restart relance le
      // script chaque jour à l'heure indiquée ; autorestart:false
      // pour ne pas boucler entre deux créneaux.
      // ------------------------------------------------------------
      name: "rh-refresh",
      script: "run_sql.js",
      args: "sql/rh_tables_refresh.sql",
      cwd: "/home/diva/amine_moussa/erp-ai-assistant/db-automation",
      interpreter: "node",
      cron_restart: "0 2 * * *",
      autorestart: false,
      watch: false,
      log_file: "/home/diva/amine_moussa/erp-ai-assistant/logs/rh-refresh.log",
      time: true
    },
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