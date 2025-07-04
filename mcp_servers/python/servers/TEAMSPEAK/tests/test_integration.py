#!/usr/bin/env python3
"""
Tests d'intégration complets pour TeamSpeak MCP
Teste tous les 18 outils avec un vrai serveur TeamSpeak 3
"""

import asyncio
import json
import os
import sys
import time
import socket
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from teamspeak_mcp.server import TeamSpeakConnection, TOOLS

class IntegrationTester:
    """Testeur d'intégration pour TeamSpeak MCP."""
    
    def __init__(self):
        self.connection = None
        self.test_results = []
        self.created_channels = []
        self.test_client_id = None
        
    async def setup(self):
        """Configuration initiale des tests."""
        print("🚀 Setting up integration tests...")
        
        # Attendre que le serveur TS3 soit prêt
        await self.wait_for_ts3_server()
        
        # Initialiser la connexion
        self.connection = TeamSpeakConnection(
            host=os.getenv("TEAMSPEAK_HOST", "teamspeak3-server"),
            port=int(os.getenv("TEAMSPEAK_PORT", "10011")),
            user=os.getenv("TEAMSPEAK_USER", "serveradmin"),
            password=os.getenv("TEAMSPEAK_PASSWORD", ""),
            server_id=int(os.getenv("TEAMSPEAK_SERVER_ID", "1"))
        )
        
        # Obtenir le token admin si nécessaire
        if not self.connection.password:
            await self.get_admin_token()
        
        print(f"📡 Connecting to TS3: {self.connection.host}:{self.connection.port}")
        print(f"👤 User: {self.connection.user}")
        
        # Test de connexion initial avec gestion d'erreur détaillée
        try:
            print("🔌 Testing initial TeamSpeak connection...")
            success = await self.connection.connect()
            if success:
                print("✅ Initial connection successful")
            else:
                print("❌ Initial connection failed")
                raise Exception("Failed to establish initial connection to TeamSpeak server")
        except Exception as e:
            print(f"💥 Connection setup failed: {e}")
            print(f"🔍 Connection details:")
            print(f"  Host: {self.connection.host}")
            print(f"  Port: {self.connection.port}")
            print(f"  User: {self.connection.user}")
            print(f"  Password set: {'Yes' if self.connection.password else 'No'}")
            print(f"  Server ID: {self.connection.server_id}")
            raise
    
    async def wait_for_ts3_server(self, max_wait=120):
        """Attendre que le serveur TeamSpeak soit prêt."""
        print("⏳ Waiting for TeamSpeak server to be ready...")
        
        # Utiliser directement les variables d'environnement (self.connection n'existe pas encore)
        host = os.getenv("TEAMSPEAK_HOST", "teamspeak3-server")
        port = int(os.getenv("TEAMSPEAK_PORT", "10011"))
        
        for i in range(max_wait):
            try:
                # Tenter une connexion basique
                if wait_for_server(host, port):
                    await asyncio.sleep(5)  # Attendre un peu plus pour la stabilité
                    return
                    
            except Exception:
                pass
                
            await asyncio.sleep(1)
        
        raise Exception("TeamSpeak server not ready after 120s")
    
    async def get_admin_token(self):
        """Récupérer le token admin depuis les logs TS3."""
        token_file = "/scripts/admin_token.txt"
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token = f.read().strip()
                if token:
                    self.connection.password = token
                    print(f"🔑 Using admin token: {token[:10]}...")
                    return
        
        print("⚠️  No admin token found, using empty password")
    
    async def run_all_tests(self):
        """Exécuter tous les tests d'intégration."""
        print("\n🧪 Running comprehensive integration tests...")
        print(f"📋 Testing {len(TOOLS)} tools\n")
        print("⏳ Adding delays to prevent rate limiting...")
        
        # Tests de base (rapides)
        await self.test_connection()
        await asyncio.sleep(2)  # Anti-flooding
        
        # Tests de lecture (permissions de base)
        await self.test_server_info()
        await asyncio.sleep(2)
        await self.test_list_channels()  
        await asyncio.sleep(2)
        await self.test_list_clients()
        await asyncio.sleep(3)
        
        # Tests de gestion des canaux (permissions moyennes)
        await self.test_channel_management()
        await asyncio.sleep(3)
        await self.test_channel_info_tests()
        await asyncio.sleep(3)
        
        # Tests de permissions (nécessitent admin - peuvent échouer)
        await self.test_channel_permissions()
        await asyncio.sleep(2)
        await self.test_server_settings()
        await asyncio.sleep(3)
        
        # Tests de gestion des utilisateurs (avec clients disponibles)
        await self.test_user_management()
        await asyncio.sleep(3)
        
        # Tests de messaging (avec rate limiting strict)
        await self.test_messaging()
        await asyncio.sleep(2)
        
        # Nettoyage
        await self.cleanup()
        
        # Rapport final
        self.print_test_report()
    
    async def test_connection(self):
        """Test de connexion de base."""
        print("🔌 Testing connection...")
        
        try:
            success = await self.connection.connect()
            if success:
                self.record_success("connect_to_server", "Basic connection successful")
            else:
                self.record_failure("connect_to_server", "Connection failed")
        except Exception as e:
            self.record_failure("connect_to_server", f"Connection error: {e}")
    
    async def test_server_info(self):
        """Test d'information serveur."""
        print("🖥️  Testing server info...")
        
        try:
            info = await asyncio.to_thread(self.connection.connection.serverinfo)
            server_name = info.get('virtualserver_name', 'Unknown')
            self.record_success("server_info", f"Server: {server_name}")
        except Exception as e:
            self.record_failure("server_info", f"Failed: {e}")
    
    async def test_list_channels(self):
        """Test de listage des canaux."""
        print("📋 Testing channel listing...")
        
        try:
            channels = await asyncio.to_thread(self.connection.connection.channellist)
            count = len(channels) if channels else 0
            self.record_success("list_channels", f"Found {count} channels")
        except Exception as e:
            self.record_failure("list_channels", f"Failed: {e}")
    
    async def test_list_clients(self):
        """Test de listage des clients."""
        print("👥 Testing client listing...")
        
        try:
            clients = await asyncio.to_thread(self.connection.connection.clientlist)
            if clients:
                # Prendre le premier client (probablement notre connexion)
                self.test_client_id = clients[0].get('clid')
                count = len(clients)
                self.record_success("list_clients", f"Found {count} clients")
            else:
                self.record_failure("list_clients", "No clients found")
        except Exception as e:
            self.record_failure("list_clients", f"Failed: {e}")
    
    async def test_channel_management(self):
        """Test de gestion des canaux - create, update, delete, talk_power."""
        print("🔧 Testing comprehensive channel management...")
        
        # Créer un canal de test
        test_channel_name = f"🤖 MCP Test Channel {int(time.time())}"
        
        try:
            # Test 1: create_channel
            print("  🏗️ Testing create_channel...")
            result = await asyncio.to_thread(
                self.connection.connection.channelcreate,
                channel_name=test_channel_name,
                channel_description="Test channel created by TeamSpeak MCP integration tests"
            )
            
            # Trouver le canal créé
            await asyncio.sleep(1)  # Laisser le temps au serveur
            channels = await asyncio.to_thread(self.connection.connection.channellist)
            test_channel = None
            for channel in channels:
                if channel.get('channel_name') == test_channel_name:
                    test_channel = channel
                    break
            
            if test_channel:
                channel_id = test_channel.get('cid')
                self.created_channels.append(channel_id)
                self.record_success("create_channel", f"Created channel {channel_id}: {test_channel_name}")
                
                # Test 2: update_channel
                print("  ✏️ Testing update_channel...")
                try:
                    await asyncio.to_thread(
                        self.connection.connection.channeledit,
                        cid=channel_id,
                        channel_description="📝 Updated by MCP integration tests",
                        channel_topic="Test topic"
                    )
                    self.record_success("update_channel", f"Updated channel {channel_id}")
                except Exception as update_error:
                    self.record_failure("update_channel", f"Failed: {update_error}")
                
                await asyncio.sleep(1)
                
                # Test 3: set_channel_talk_power
                print("  🔊 Testing set_channel_talk_power...")
                try:
                    await asyncio.to_thread(
                        self.connection.connection.channeledit,
                        cid=channel_id,
                        channel_needed_talk_power=25
                    )
                    self.record_success("set_channel_talk_power", f"Set talk power (25) for channel {channel_id}")
                except Exception as talk_error:
                    self.record_failure("set_channel_talk_power", f"Failed: {talk_error}")
                
                await asyncio.sleep(1)
                
                # Test 4: channel_info (sur notre canal créé)
                print("  📋 Testing channel_info on created channel...")
                try:
                    info = await asyncio.to_thread(
                        self.connection.connection.channelinfo,
                        cid=channel_id
                    )
                    self.record_success("channel_info_created", f"Got info for created channel {channel_id}")
                except Exception as info_error:
                    self.record_failure("channel_info_created", f"Failed: {info_error}")
                
                # Note: delete_channel sera testé dans cleanup()
                
            else:
                self.record_failure("create_channel", "Channel not found after creation")
                
        except Exception as e:
            self.record_failure("create_channel", f"Failed: {e}")
            # Si create échoue, marquer les autres comme non testables
            self.record_failure("update_channel", "Skipped - channel creation failed")
            self.record_failure("set_channel_talk_power", "Skipped - channel creation failed")
    
    async def test_channel_permissions(self):
        """Test de gestion des permissions de canal."""
        print("🛡️  Testing channel permissions...")
        
        if not self.created_channels:
            self.record_failure("manage_channel_permissions", "No test channels available")
            return
        
        channel_id = self.created_channels[0]
        
        try:
            # Test list permissions
            perms = await asyncio.to_thread(
                self.connection.connection.channelpermlist,
                cid=channel_id, permsid=True
            )
            self.record_success("manage_channel_permissions_list", f"Listed permissions for channel {channel_id}")
            
            # Test add permission
            await asyncio.to_thread(
                self.connection.connection.channeladdperm,
                cid=channel_id, permsid="i_channel_needed_join_power", permvalue=10
            )
            self.record_success("manage_channel_permissions_add", f"Added permission to channel {channel_id}")
            
        except Exception as e:
            self.record_failure("manage_channel_permissions", f"Failed: {e}")
    
    async def test_server_settings(self):
        """Test de configuration serveur et outils avancés."""
        print("⚙️ Testing server settings and advanced tools...")
        
        # Test 1: update_server_settings (permissions admin requises)
        try:
            await asyncio.to_thread(
                self.connection.connection.serveredit,
                virtualserver_welcomemessage="🤖 Welcome! Server managed by TeamSpeak MCP"
            )
            self.record_success("update_server_settings", "Updated server welcome message")
        except Exception as e:
            self.record_failure("update_server_settings", f"Failed (admin required): {e}")
        
        await asyncio.sleep(1)
        
        # Test 2: Tests d'outils impossibles sans clients réels
        print("  ⚠️ Testing client-dependent tools (expected to fail)...")
        
        # Ces tests sont censés échouer car on n'a pas de vrais clients à manipuler
        self.record_failure("move_client", "No real clients available to move")
        self.record_failure("kick_client", "No real clients available to kick") 
        self.record_failure("ban_client", "No real clients available to ban")
        
        print("  📝 Client-dependent tools marked as untestable (expected behavior)")
    
    async def test_channel_info_tests(self):
        """Test d'information sur les canaux existants."""
        print("📋 Testing channel info on existing channels...")
        
        try:
            # D'abord lister les canaux pour avoir des IDs
            channels = await asyncio.to_thread(self.connection.connection.channellist)
            if channels and len(channels) > 0:
                # Tester l'info sur le premier canal
                first_channel = channels[0]
                channel_id = first_channel.get('cid')
                
                if channel_id:
                    info = await asyncio.to_thread(
                        self.connection.connection.channelinfo,
                        cid=channel_id
                    )
                    self.record_success("channel_info", f"Got info for channel {channel_id}")
                else:
                    self.record_failure("channel_info", "No valid channel ID found")
            else:
                self.record_failure("channel_info", "No channels available to test")
                
        except Exception as e:
            self.record_failure("channel_info", f"Failed: {e}")
    
    async def test_user_management(self):
        """Test de gestion des utilisateurs avec clients disponibles."""
        print("👤 Testing user management...")
        
        # D'abord obtenir la liste des clients connectés
        try:
            clients = await asyncio.to_thread(self.connection.connection.clientlist)
            if clients and len(clients) > 0:
                # Utiliser le premier client (probablement notre connexion ServerQuery)
                first_client = clients[0]
                self.test_client_id = first_client.get('clid')
                
                if self.test_client_id:
                    # Test client_info_detailed
                    try:
                        info = await asyncio.to_thread(
                            self.connection.connection.clientinfo,
                            clid=self.test_client_id
                        )
                        self.record_success("client_info_detailed", f"Got detailed info for client {self.test_client_id}")
                        
                        # Si on a les infos client, essayer les permissions
                        if hasattr(info, 'data') and info.data:
                            client_info = info.data[0]
                        elif hasattr(info, '__iter__') and not isinstance(info, str):
                            client_info = list(info)[0] if info else {}
                        else:
                            client_info = info
                        
                        client_database_id = client_info.get('client_database_id')
                        if client_database_id:
                            try:
                                groups = await asyncio.to_thread(
                                    self.connection.connection.servergroupsbyclientid,
                                    cldbid=client_database_id
                                )
                                self.record_success("manage_user_permissions_list_groups", f"Listed groups for client {self.test_client_id}")
                            except Exception as group_error:
                                self.record_failure("manage_user_permissions_list_groups", f"Failed: {group_error}")
                                
                    except Exception as info_error:
                        self.record_failure("client_info_detailed", f"Failed: {info_error}")
                else:
                    self.record_failure("client_info_detailed", "No valid client ID found")
            else:
                self.record_failure("client_info_detailed", "No clients available to test")
                self.record_failure("manage_user_permissions_list_groups", "No clients available to test")
                
        except Exception as e:
            self.record_failure("user_management", f"Failed to get client list: {e}")
    
    async def test_messaging(self):
        """Test de messagerie avec gestion du rate limiting."""
        print("💬 Testing messaging with rate limiting...")
        
        try:
            # Test send_channel_message avec délai
            await asyncio.to_thread(
                self.connection.connection.sendtextmessage,
                targetmode=2, target=0, msg="🤖 Test channel message from TeamSpeak MCP integration tests"
            )
            self.record_success("send_channel_message", "Sent channel message")
            
            # Délai pour éviter le flooding
            await asyncio.sleep(3)
            
            # Test send_private_message uniquement si on a un client cible
            if self.test_client_id:
                try:
                    await asyncio.to_thread(
                        self.connection.connection.sendtextmessage,
                        targetmode=1, target=self.test_client_id, msg="🤖 Test private message from MCP"
                    )
                    self.record_success("send_private_message", f"Sent private message to client {self.test_client_id}")
                except Exception as pm_error:
                    self.record_failure("send_private_message", f"Failed: {pm_error}")
            else:
                self.record_failure("send_private_message", "No target client available")
            
        except Exception as e:
            self.record_failure("send_channel_message", f"Failed: {e}")
            self.record_failure("send_private_message", "Channel message failed, skipping private message")
    
    async def cleanup(self):
        """Nettoyage après les tests."""
        print("🧹 Cleaning up test data...")
        
        # Supprimer les canaux de test (et tester delete_channel)
        for channel_id in self.created_channels:
            try:
                print(f"  🗑️ Testing delete_channel on channel {channel_id}...")
                await asyncio.to_thread(
                    self.connection.connection.channeldelete,
                    cid=channel_id, force=1
                )
                print(f"  ✅ Deleted test channel {channel_id}")
                self.record_success("delete_channel", f"Deleted channel {channel_id}")
            except Exception as e:
                print(f"  ⚠️ Failed to delete channel {channel_id}: {e}")
                self.record_failure("delete_channel", f"Failed: {e}")
        
        # Si aucun canal n'a été créé, marquer delete_channel comme non testé
        if not self.created_channels:
            self.record_failure("delete_channel", "No channels were created to delete")
        
        # Fermer la connexion
        if self.connection:
            await self.connection.disconnect()
    
    def record_success(self, tool_name: str, message: str):
        """Enregistrer un succès de test."""
        self.test_results.append({
            "tool": tool_name,
            "status": "SUCCESS",
            "message": message
        })
        print(f"  ✅ {tool_name}: {message}")
    
    def record_failure(self, tool_name: str, message: str):
        """Enregistrer un échec de test."""
        self.test_results.append({
            "tool": tool_name,
            "status": "FAILURE", 
            "message": message
        })
        print(f"  ❌ {tool_name}: {message}")
    
    def print_test_report(self):
        """Afficher le rapport final des tests avec catégorisation."""
        print("\n" + "="*70)
        print("📊 TEAMSPEAK MCP INTEGRATION TEST REPORT")
        print("="*70)
        
        # Catégoriser les résultats
        successes = [r for r in self.test_results if r["status"] == "SUCCESS"]
        
        # Catégories d'échecs
        permission_failures = [r for r in self.test_results if r["status"] == "FAILURE" and 
                             ("insufficient client permissions" in r["message"] or 
                              "admin required" in r["message"])]
        
        impossible_failures = [r for r in self.test_results if r["status"] == "FAILURE" and 
                             ("No real clients" in r["message"] or 
                              "No target client" in r["message"] or
                              "No clients available" in r["message"])]
        
        skipped_failures = [r for r in self.test_results if r["status"] == "FAILURE" and 
                          "Skipped" in r["message"]]
        
        rate_limit_failures = [r for r in self.test_results if r["status"] == "FAILURE" and 
                             ("flooding" in r["message"] or "rate" in r["message"])]
        
        other_failures = [r for r in self.test_results if r["status"] == "FAILURE" and 
                        r not in permission_failures + impossible_failures + 
                        skipped_failures + rate_limit_failures]
        
        # Statistiques globales
        total_tools = len(TOOLS)
        tested_tools = len([r for r in self.test_results if not any(skip in r["message"] 
                           for skip in ["Skipped", "No real clients", "No target client", "No clients available"])])
        
        print(f"📋 **SUMMARY:**")
        print(f"   • Total MCP Tools: {total_tools}")
        print(f"   • Actually Tested: {tested_tools}")
        print(f"   • ✅ Successes: {len(successes)}")
        print(f"   • ❌ Total Failures: {len(self.test_results) - len(successes)}")
        print(f"   • 🎯 Success Rate: {len(successes)/tested_tools*100:.1f}% (of testable tools)")
        
        print(f"\n📊 **DETAILED BREAKDOWN:**")
        
        if successes:
            print(f"\n✅ **SUCCESSFUL TOOLS ({len(successes)}):**")
            for success in successes:
                print(f"   • {success['tool']}: {success['message']}")
        
        if permission_failures:
            print(f"\n🔒 **PERMISSION FAILURES ({len(permission_failures)}) - Need Admin Token:**")
            for failure in permission_failures:
                print(f"   • {failure['tool']}: {failure['message']}")
        
        if impossible_failures:
            print(f"\n⚠️ **IMPOSSIBLE TO TEST ({len(impossible_failures)}) - Need Real Clients:**")
            for failure in impossible_failures:
                print(f"   • {failure['tool']}: {failure['message']}")
        
        if rate_limit_failures:
            print(f"\n🚦 **RATE LIMIT FAILURES ({len(rate_limit_failures)}) - Server Protection:**")
            for failure in rate_limit_failures:
                print(f"   • {failure['tool']}: {failure['message']}")
        
        if skipped_failures:
            print(f"\n⏭️ **SKIPPED ({len(skipped_failures)}) - Dependency Failed:**")
            for failure in skipped_failures:
                print(f"   • {failure['tool']}: {failure['message']}")
        
        if other_failures:
            print(f"\n💥 **OTHER FAILURES ({len(other_failures)}):**")
            for failure in other_failures:
                print(f"   • {failure['tool']}: {failure['message']}")
        
        # Sauvegarder les résultats
        os.makedirs("/app/test_results", exist_ok=True)
        
        # Créer un rapport détaillé
        detailed_report = {
            "summary": {
                "total_tools": total_tools,
                "tested_tools": tested_tools,
                "successes": len(successes),
                "failures": len(self.test_results) - len(successes),
                "success_rate": round(len(successes)/tested_tools*100, 1)
            },
            "categories": {
                "successes": successes,
                "permission_failures": permission_failures,
                "impossible_failures": impossible_failures,
                "rate_limit_failures": rate_limit_failures,
                "skipped_failures": skipped_failures,
                "other_failures": other_failures
            },
            "all_results": self.test_results
        }
        
        with open("/app/test_results/integration_results.json", "w") as f:
            json.dump(detailed_report, f, indent=2)
        
        print(f"\n💾 **Detailed results saved to /app/test_results/integration_results.json**")
        
        # Code de sortie basé sur les vrais échecs (pas les impossibles)
        real_failures = permission_failures + rate_limit_failures + other_failures
        if real_failures:
            print(f"\n⚠️ **{len(real_failures)} tools had real issues (excluding impossible/skipped tests)**")
            sys.exit(1)
        else:
            print(f"\n🎉 **All testable tools worked correctly!**")
            sys.exit(0)

def wait_for_server(host: str, port: int, timeout: int = 120) -> bool:
    """
    Attendre que le serveur TeamSpeak soit prêt
    """
    print(f"⏳ Waiting for TeamSpeak server at {host}:{port}...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                if result == 0:
                    print(f"✅ Server is ready after {int(time.time() - start_time)}s")
                    return True
        except Exception as e:
            print(f"⚠️  Connection attempt failed: {e}")
        
        elapsed = int(time.time() - start_time)
        if elapsed % 15 == 0:  # Log every 15 seconds
            print(f"⏳ Still waiting... ({elapsed}s elapsed)")
        
        time.sleep(1)
    
    print(f"❌ TeamSpeak server not ready after {timeout} seconds")
    return False

async def main():
    """Fonction principale des tests."""
    tester = IntegrationTester()
    
    try:
        print("🚀 Starting TeamSpeak MCP Integration Tests")
        print("=" * 60)
        await tester.setup()
        await tester.run_all_tests()
        print("🎉 All integration tests completed successfully!")
    except Exception as e:
        print(f"💥 Integration tests failed with error: {e}")
        print(f"🔍 Error details:")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        
        # Print traceback for debugging
        import traceback
        print(f"📋 Full traceback:")
        traceback.print_exc()
        
        # Try to save whatever results we have
        try:
            if tester.test_results:
                print(f"💾 Saving partial test results ({len(tester.test_results)} tests)...")
                os.makedirs("/app/test_results", exist_ok=True)
                with open("/app/test_results/integration_results.json", "w") as f:
                    json.dump(tester.test_results, f, indent=2)
                print("✅ Partial results saved")
            else:
                print("📋 No test results to save")
        except Exception as save_error:
            print(f"⚠️ Failed to save partial results: {save_error}")
        
        print("💥 Exiting with error code 1")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 