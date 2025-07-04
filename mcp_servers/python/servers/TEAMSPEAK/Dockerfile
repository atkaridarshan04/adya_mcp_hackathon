# Image de base Python
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Nicolas Varrot"
LABEL description="MCP Server pour contrôler TeamSpeak depuis des modèles d'IA"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Créer un utilisateur non-root pour la sécurité
RUN useradd --create-home --shell /bin/bash mcp

# Répertoire de travail
WORKDIR /app

# Copier les fichiers de requirements en premier pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances système et Python
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        netcat-openbsd \
        iputils-ping \
        dnsutils \
        wget \
        curl && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y gcc libc6-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copier le script d'entrée
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Copier le code source principal
COPY teamspeak_mcp/ ./teamspeak_mcp/
COPY test_mcp.py .

# Ajouter le répertoire app au PYTHONPATH pour que le module soit trouvé
ENV PYTHONPATH="/app:$PYTHONPATH"

# Créer les permissions appropriées
RUN chown -R mcp:mcp /app

# Changer vers l'utilisateur non-root
USER mcp

# Point d'entrée avec le script personnalisé
ENTRYPOINT ["docker-entrypoint.sh"]

# Commande par défaut (mode serveur)
CMD ["server"]

# Healthcheck amélioré
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD docker-entrypoint.sh config > /dev/null || exit 1

# Exposer les variables d'environnement attendues (documentation)
ENV TEAMSPEAK_HOST=""
ENV TEAMSPEAK_PORT="10011"
ENV TEAMSPEAK_USER="serveradmin"
ENV TEAMSPEAK_PASSWORD=""
ENV TEAMSPEAK_SERVER_ID="1" 