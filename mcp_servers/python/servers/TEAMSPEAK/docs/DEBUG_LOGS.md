# 🔍 Debug TeamSpeak ServerQuery Logs - Guide Complet

## Problème
Votre MCP TeamSpeak ne récupère que 2-3 lignes de logs via l'API ServerQuery, alors que l'interface client TeamSpeak montre des dizaines d'entrées détaillées.

## 🚨 Causes Possibles

### 1. Configuration côté serveur TeamSpeak
- **Logging désactivé** : Les logs ne sont pas activés sur le serveur
- **Niveau de log insuffisant** : Seuls les erreurs critiques sont loggées
- **Rotation des logs** : Les logs sont supprimés trop rapidement
- **Configuration ts3server.ini** : Paramètres de logging incorrects

### 2. Limitations ServerQuery
- **Permissions insuffisantes** : Le compte ServerQuery n'a pas accès aux logs complets
- **Filtrage automatique** : TeamSpeak filtre certains événements pour ServerQuery
- **Différence virtual server vs instance** : Les logs sont stockés à différents niveaux

### 3. Problème dans le code MCP
- **Extraction incorrecte** : Les données ne sont pas correctement extraites
- **Paramètres manquants** : Certains paramètres de logview ne sont pas utilisés

## 🛠️ Solutions Étape par Étape

### Étape 1: Diagnostic Automatique

Utilisez le script de diagnostic fourni :

```bash
# Diagnostic rapide
python3 scripts/diagnose_logs.py --password YOUR_SERVERQUERY_PASSWORD

# Diagnostic complet avec paramètres personnalisés
python3 scripts/diagnose_logs.py \
    --host your-server.com \
    --port 10011 \
    --user serveradmin \
    --password YOUR_PASSWORD \
    --server-id 1
```

### Étape 2: Vérification Configuration Serveur

#### Via Client TeamSpeak
1. Connectez-vous en tant qu'admin
2. Clic droit sur le nom du serveur → **Edit Virtual Server**
3. Cliquez sur **More** en bas
4. Onglet **Logs**
5. Activez tous les types de logs nécessaires :
   - ✅ Client connections
   - ✅ Client disconnections
   - ✅ Channel created/edited/deleted
   - ✅ Server edited
   - ✅ Permissions changed
   - ✅ File transfers

#### Via ServerQuery
```bash
# Se connecter via telnet
telnet your-server.com 10011

# Se logger
login serveradmin YOUR_PASSWORD

# Sélectionner le serveur virtuel
use sid=1

# Vérifier la configuration
serverinfo

# Modifier les paramètres de logging
serveredit virtualserver_log_client=1 virtualserver_log_query=1 virtualserver_log_channel=1 virtualserver_log_permissions=1 virtualserver_log_server=1 virtualserver_log_filetransfer=1
```

### Étape 3: Configuration ts3server.ini

Ajoutez ou modifiez ces paramètres dans votre `ts3server.ini` :

```ini
# Logging configuration
logpath=logs/
logquerycommands=1
logappend=1
loglevels=4  # 1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO

# Log retention
dbclientkeepdays=90
dblogkeepdays=30

# Instance logging
instance_logappend=1
instance_logpath=logs/
```

### Étape 4: Test avec MCP amélioré

Utilisez les nouveaux outils MCP :

```bash
# Diagnostic de la configuration
# Dans votre client AI, utilisez:
diagnose_log_configuration

# Configuration automatique
configure_server_logging

# Test des logs d'instance
get_instance_logs

# Logs enhanced avec filtres
view_server_logs lines=100 log_level=4 instance_log=false
```

### Étape 5: Permissions ServerQuery

Vérifiez que votre compte ServerQuery a ces permissions :

- `b_virtualserver_info_view`
- `b_virtualserver_log_view` (si disponible)
- `i_server_log_view_power` (si disponible)
- `b_serverinstance_log_view` (pour les logs d'instance)

## 🔧 Paramètres Avancés logview

### Paramètres Standard
```python
logview(
    lines=100,        # Nombre de lignes (1-100)
    reverse=1,        # 1=newest first, 0=oldest first
    instance=1,       # 1=instance logs, 0=virtual server logs
    begin_pos=0       # Position de début dans le fichier
)
```

### Paramètres Expérimentaux (TeamSpeak 3.13+)
```python
logview(
    loglevel=4,           # Niveau: 1=ERROR, 2=WARNING, 3=DEBUG, 4=INFO
    timestamp_begin=...,  # Unix timestamp début
    timestamp_end=...,    # Unix timestamp fin
    filter_level=...,     # Filtrage par niveau
    filter_msg=...,       # Filtrage par message
)
```

## 📊 Comparaison Client vs ServerQuery

| Fonctionnalité | Client TS | ServerQuery |
|----------------|-----------|-------------|
| Connexions clients | ✅ | ✅ (si configuré) |
| Modifications canaux | ✅ | ✅ (si configuré) |
| Changements groupes | ✅ | ⚠️ (limité) |
| Permissions | ✅ | ⚠️ (limité) |
| Mouvements clients | ✅ | ✅ (si configuré) |
| Messages privés | ✅ | ❌ (privacité) |
| Logs en temps réel | ✅ | ❌ (polling only) |

## 🚨 Problèmes Courants et Solutions

### "Pas de logs trouvés"
- ✅ Vérifiez que le logging est activé
- ✅ Redémarrez le serveur TeamSpeak
- ✅ Vérifiez les permissions du dossier logs/

### "Seulement 2-3 lignes"
- ✅ Utilisez `instance_log=true`
- ✅ Augmentez `lines=100`
- ✅ Vérifiez la rotation des logs

### "Logs incomplets par rapport au client"
- ✅ Le client montre TOUS les événements, ServerQuery seulement ceux configurés
- ✅ Activez plus de types de logs côté serveur
- ✅ Utilisez les notifications en temps réel avec `servernotifyregister`

### "Erreur de permissions"
- ✅ Utilisez le compte `serveradmin`
- ✅ Ajoutez les permissions de logs au groupe
- ✅ Vérifiez `query_ip_whitelist.txt`

## 🔄 Alternative: Notifications en Temps Réel

Au lieu de polling les logs, utilisez les notifications :

```python
# S'enregistrer pour les notifications
servernotifyregister event=server
servernotifyregister event=channel id=0
servernotifyregister event=textserver
servernotifyregister event=textchannel
```

Ces notifications vous donneront les événements en temps réel comme le client TeamSpeak.

## 📝 Configuration Optimale

### ts3server.ini recommandé
```ini
# Logging complet
logpath=logs/
logquerycommands=1
logappend=1
logclientconnections=1
logclientdisconnections=1
logchannelcreated=1
logchanneledited=1
logchanneldeleted=1
logserveredited=1
logpermissions=1
logfiletransfer=1

# Retention
dblogkeepdays=30
dbclientkeepdays=90

# Performance
logbuffer=64
logsync=1
```

### Paramètres serveur recommandés
```bash
serveredit \
  virtualserver_log_client=1 \
  virtualserver_log_query=1 \
  virtualserver_log_channel=1 \
  virtualserver_log_permissions=1 \
  virtualserver_log_server=1 \
  virtualserver_log_filetransfer=1
```

## ✅ Checklist de Vérification

- [ ] Logging activé dans ts3server.ini
- [ ] Permissions ServerQuery correctes
- [ ] Configuration serveur virtuel activée
- [ ] Redémarrage du serveur après modifications
- [ ] Test avec script de diagnostic
- [ ] Comparaison logs instance vs virtual server
- [ ] Vérification espace disque disponible
- [ ] Test avec différents niveaux de log

## 🆘 Support Avancé

Si le problème persiste après avoir suivi ce guide :

1. **Collectez les informations** :
   ```bash
   python3 scripts/diagnose_logs.py --password YOUR_PASSWORD > debug_logs.txt
   ```

2. **Vérifiez les logs système** :
   ```bash
   tail -f /path/to/teamspeak/logs/ts3server_*.log
   ```

3. **Testez avec telnet direct** :
   ```bash
   telnet your-server.com 10011
   # puis testez manuellement logview
   ```

4. **Comparez avec YaTQA** ou autre outil ServerQuery pour vérifier si le problème est spécifique au MCP.

L'objectif est d'obtenir le même niveau de détail que l'interface client TeamSpeak, ou au minimum beaucoup plus d'informations qu'actuellement. 