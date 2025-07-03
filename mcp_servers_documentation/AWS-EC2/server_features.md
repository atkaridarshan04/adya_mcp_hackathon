# AWS-EC2 MCP Server - Server Features

## Overview

A comprehensive Model Context Protocol server that enables AI assistants to interact with AWS services through intelligent command execution. This server provides extensive AWS infrastructure management capabilities with natural language processing and supports 50+ distinct operations across multiple AWS services.

## Core Capabilities

### EC2 Instance Management
Complete EC2 instance lifecycle operations with advanced configuration options.

**Operations Available:**
- Create instances with custom configurations and user data
- List and filter instances by status, type, tags, and regions
- Start, stop, reboot, and terminate instances
- Modify instance attributes and types
- Instance status monitoring and health checks
- Bulk instance operations across multiple resources
- Instance metadata management and retrieval

### Security Groups Management
Comprehensive security group administration and network access control.

**Operations Available:**
- Create security groups with custom descriptions
- List security groups with detailed rule information
- Add inbound and outbound rules with protocol specifications
- Remove specific security rules and manage access
- Delete security groups with dependency checks
- Security group search and filtering by VPC
- Rule validation and conflict detection

### Key Pairs Management
SSH key pair administration for secure instance access.

**Operations Available:**
- Create new key pairs for instance access
- List existing key pairs with fingerprint information
- Delete key pairs with safety validations
- Import external public keys
- Key pair metadata and usage tracking

### VPC and Networking Operations
Virtual Private Cloud and network infrastructure management.

**Operations Available:**
- List VPCs with CIDR blocks and configurations
- Subnet management and availability zone operations
- Route table creation and rule management
- Internet gateway attachment and configuration
- NAT gateway operations for private subnets
- Network ACL management and rule configuration
- VPC peering and cross-region connectivity

### EBS Volume Management
Elastic Block Store operations and storage administration.

**Operations Available:**
- Create EBS volumes with custom size and type specifications
- List volumes with filtering by status and attachment state
- Attach and detach volumes to running instances
- Create snapshots for backup and recovery
- Delete volumes with safety checks and confirmations
- Volume encryption management and key rotation
- Performance monitoring and IOPS configuration

### AMI Operations
Amazon Machine Image management and custom image creation.

**Operations Available:**
- List available AMIs with filtering by owner and architecture
- Create custom AMIs from running instances
- Copy AMIs across different AWS regions
- Deregister AMIs and cleanup associated snapshots
- AMI sharing permissions and cross-account access
- Image lifecycle management and automation

### S3 Storage Operations
Simple Storage Service bucket and object management.

**Operations Available:**
- List S3 buckets with region and creation information
- Create buckets with versioning and encryption settings
- Upload and download objects with metadata
- Manage bucket policies and access permissions
- Object lifecycle management and archiving
- Cross-region replication configuration

### IAM Management
Identity and Access Management for security and permissions.

**Operations Available:**
- List users, roles, and policies
- Create and manage IAM users and groups
- Attach and detach policies from users and roles
- Generate access keys and manage credentials
- Role assumption and cross-account access
- Policy creation and permission management

### CloudWatch Monitoring
Monitoring, logging, and alerting capabilities.

**Operations Available:**
- Retrieve instance metrics and performance data
- Create custom alarms and notifications
- Log group management and log streaming
- Dashboard creation and metric visualization
- Event monitoring and automated responses
- Cost and billing metric tracking


## Technical Architecture

### Command Execution Engine
- **aws_cli_pipeline**: Execute any AWS CLI command with Unix pipeline support
- **aws_cli_help**: Comprehensive AWS documentation and help system
- Dynamic credential injection and multi-account support
- Timeout management and error handling
- Command validation and security checks

### Pipeline Operations
Advanced command chaining and data processing capabilities:
- Complex filtering with grep, awk, and jq
- Data transformation and formatting
- Multi-command workflows and automation
- Output processing and report generation

## Authentication & Security

### Credential Management
- Dynamic credential injection per request
- Multi-account and cross-region support
- IAM role assumption for enhanced security
- Environment variable and profile support
- No credential storage on server

## Prerequisites

- Python 3.8 or higher
- AWS CLI v2 installed 
- AWS account with appropriate IAM permissions
- Network access to AWS APIs and services

## Use Cases

### Infrastructure Management
- Automated resource provisioning and configuration
- Infrastructure scaling and optimization
- Multi-environment deployment automation
- Resource lifecycle management