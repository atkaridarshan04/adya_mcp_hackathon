#!/usr/bin/env python3
"""
Script de diagnostic pour les logs TeamSpeak ServerQuery

Ce script aide à diagnostiquer pourquoi les logs ne sont pas récupérés
complètement via l'API ServerQuery.
"""

import asyncio
import sys
import os
import argparse
import ts3

async def test_log_methods(host, port, user, password, server_id):
    """Test différentes méthodes de récupération des logs."""
    print("🔍 Démarrage du diagnostic des logs TeamSpeak...")
    
    try:
        # Connexion au serveur
        connection = ts3.query.TS3Connection(host, port)
        connection.use(sid=server_id)
        
        if password:
            try:
                connection.login(client_login_name=user, client_login_password=password)
                print("✅ Authentification réussie avec login/password")
            except Exception as e:
                print(f"⚠️  Authentification login/password échouée: {e}")
                try:
                    connection.tokenuse(token=password)
                    print("✅ Authentification réussie avec token")
                except Exception as token_error:
                    print(f"❌ Authentification token échouée: {token_error}")
                    return
        
        print("\n📊 Tests de récupération des logs...")
        
        # Test 1: Logs basiques
        print("\n1. Test logs basiques (50 lignes):")
        try:
            response = connection.logview(lines=50)
            print(f"   Type de réponse: {type(response)}")
            print(f"   Contenu brut: {str(response)[:200]}...")
            
            if hasattr(response, 'parsed'):
                print(f"   Parsed disponible: {response.parsed}")
                if response.parsed:
                    log_data = response.parsed[0]
                    print(f"   Keys dans log_data: {list(log_data.keys()) if isinstance(log_data, dict) else 'Non dict'}")
                    if 'l' in log_data:
                        log_lines = log_data['l'].split('\\n')
                        print(f"   ✅ {len(log_lines)} lignes trouvées dans 'l'")
                        for i, line in enumerate(log_lines[:5], 1):
                            if line.strip():
                                print(f"      {i}. {line.strip()}")
                    else:
                        print("   ❌ Pas de champ 'l' trouvé")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 2: Logs avec reverse=false
        print("\n2. Test logs reverse=false:")
        try:
            response = connection.logview(lines=50, reverse=0)
            if hasattr(response, 'parsed') and response.parsed:
                log_data = response.parsed[0]
                if 'l' in log_data:
                    log_lines = log_data['l'].split('\\n')
                    print(f"   ✅ {len(log_lines)} lignes trouvées")
                else:
                    print("   ❌ Pas de champ 'l' trouvé")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 3: Logs d'instance
        print("\n3. Test logs d'instance:")
        try:
            response = connection.logview(lines=50, instance=1)
            if hasattr(response, 'parsed') and response.parsed:
                log_data = response.parsed[0]
                if 'l' in log_data:
                    log_lines = log_data['l'].split('\\n')
                    print(f"   ✅ {len(log_lines)} lignes trouvées")
                else:
                    print("   ❌ Pas de champ 'l' trouvé")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 4: Logs avec différents niveaux
        print("\n4. Test logs avec niveaux spécifiques:")
        for level in [1, 2, 3, 4]:
            try:
                response = connection.logview(lines=50, loglevel=level)
                if hasattr(response, 'parsed') and response.parsed:
                    log_data = response.parsed[0]
                    if 'l' in log_data:
                        log_lines = log_data['l'].split('\\n')
                        print(f"   Niveau {level}: {len(log_lines)} lignes")
                    else:
                        print(f"   Niveau {level}: Pas de champ 'l'")
            except Exception as e:
                print(f"   Niveau {level}: Erreur - {e}")
        
        # Test 5: Configuration du serveur
        print("\n5. Vérification de la configuration du serveur:")
        try:
            response = connection.serverinfo()
            if hasattr(response, 'parsed') and response.parsed:
                info = response.parsed[0]
                log_related = {k: v for k, v in info.items() if 'log' in k.lower()}
                if log_related:
                    print("   Configuration liée aux logs:")
                    for key, value in log_related.items():
                        print(f"     {key}: {value}")
                else:
                    print("   ❌ Aucune configuration de logs trouvée")
        except Exception as e:
            print(f"   ❌ Erreur lors de la récupération des infos serveur: {e}")
        
        # Test 6: Test avec plus de lignes
        print("\n6. Test avec plus de lignes (100):")
        try:
            response = connection.logview(lines=100)
            if hasattr(response, 'parsed') and response.parsed:
                log_data = response.parsed[0]
                if 'l' in log_data:
                    log_lines = log_data['l'].split('\\n')
                    print(f"   ✅ {len(log_lines)} lignes trouvées avec 100 lignes demandées")
                    
                    # Analyser les types d'événements
                    event_types = {}
                    for line in log_lines:
                        if '|' in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                event_type = parts[2].strip()
                                event_types[event_type] = event_types.get(event_type, 0) + 1
                    
                    print("   Types d'événements trouvés:")
                    for event_type, count in event_types.items():
                        print(f"     {event_type}: {count}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
        
        # Test 7: Recommandations
        print("\n7. 📋 Recommandations:")
        print("   - Vérifiez les paramètres de logging dans ts3server.ini")
        print("   - Consultez les logs du client TeamSpeak pour comparaison")
        print("   - Vérifiez les permissions du compte ServerQuery")
        print("   - Considérez utiliser les logs d'instance (instance=1)")
        print("   - Testez avec different niveaux de log (loglevel=1-4)")
        
        connection.quit()
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

def main():
    """Point d'entrée du script."""
    parser = argparse.ArgumentParser(description="Diagnostic des logs TeamSpeak ServerQuery")
    parser.add_argument("--host", default="localhost", help="Adresse du serveur TeamSpeak")
    parser.add_argument("--port", type=int, default=10011, help="Port ServerQuery")
    parser.add_argument("--user", default="serveradmin", help="Nom d'utilisateur ServerQuery")
    parser.add_argument("--password", required=True, help="Mot de passe ServerQuery")
    parser.add_argument("--server-id", type=int, default=1, help="ID du serveur virtuel")
    
    args = parser.parse_args()
    
    print("🚀 Script de diagnostic des logs TeamSpeak")
    print(f"   Serveur: {args.host}:{args.port}")
    print(f"   Utilisateur: {args.user}")
    print(f"   Serveur ID: {args.server_id}")
    print()
    
    asyncio.run(test_log_methods(
        args.host, 
        args.port, 
        args.user, 
        args.password, 
        args.server_id
    ))

if __name__ == "__main__":
    main() 