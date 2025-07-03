# AWS-EC2 MCP Server – Demos and Payload Examples

## 🎥 Demo Video
- **MCP server setup explanation + API Execution + Features Testing**: [Watch Here](https://drive.google.com/file/d/1Aypz5dYoAEE86JRd01c7ZKZMkt3zrGze/view?usp=sharing)

---

## 🎥 Credentials Gathering Video
- **Gathering Credentials & Setup(Full end-to-end video)**: [Watch Here](https://drive.google.com/file/d/1Abg6Ny7VcBXJMJ1XiA2BgXrksjdpuIhm/view?usp=sharing)

---

## 🔐 Credential JSON Payload
Example payload format for sending credentials to the MCP Server which going to be use it in Client API paylod:
```json
{
  "AWS-EC2": {
    "aws_access_key_id": "your_aws_access_key_id",
    "aws_secret_access_key": "your_aws_secret_access_key",
    "aws_region": "aws_region"
    }
}
```
