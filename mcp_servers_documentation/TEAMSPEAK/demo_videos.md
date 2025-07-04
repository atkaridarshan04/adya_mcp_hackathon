# TEAMSPEAK MCP Server – Demos and Payload Examples

## 🎥 Demo Video
- **MCP server setup explanation + API Execution + Features Testing**: [Watch Here](https://drive.google.com/file/d/1VJYpuMiDazJhP0K4-bRVdWuJIXbBgHz7/view?usp=sharing)

---

## 🎥 Credentials Gathering Video
- **Gathering Credentials & Setup(Full end-to-end video)**: [Watch Here](https://drive.google.com/file/d/17YKctUxinQTfKZvBqqFi07l8lrme_26w/view?usp=sharing)

---

## 🔐 Credential JSON Payload
Example payload format for sending credentials to the MCP Server which going to be use it in Client API paylod:
```json
{
  "TEAMSPEAK": {
    "host": "teamspeak_host",
    "port": "teamspeak_port", // default 10011
    "user": "teamspeak_user", 
    "password": "teamspeak_password",
    "server_id": "teamspeak_server_id" // default 1
  }
}
```
