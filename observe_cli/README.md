# <img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="70" align="center" /> Observe CLI Tools for Kubiya

<div align="center">

> 🚀 Direct Observe CLI command execution through Kubiya

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Observe](https://img.shields.io/badge/Observe-Monitoring-00A3E0?style=for-the-badge&logo=observe&logoColor=white)](https://www.observeinc.com/)
[![CLI](https://img.shields.io/badge/CLI-Powered-326CE5?style=for-the-badge&logo=terminal&logoColor=white)](https://github.com/observeinc/cli)

</div>

## 🎯 Overview

This module provides a direct CLI wrapper for Observe commands through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, this tool enables direct execution of any Observe CLI command with full access to all Observe features and capabilities.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#00A3E0', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|CLI Command| B[Observe CLI]
    B -->|Execute| C[Any Observe Command]
    B -->|Return| D[Command Output]
    
    style A fill:#00A3E0,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#00A3E0,color:#fff,stroke-width:2px
    style D fill:#00A3E0,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🔧 Universal CLI Access
- Execute any Observe CLI command
- Full command-line functionality
- Direct access to all features
- Real-time command execution

</td>
<td width="50%">

### 🚀 Seamless Integration
- Native Observe CLI experience
- Command validation
- Error handling
- Output formatting

</td>
</tr>
<tr>
<td width="50%">

### 📊 Complete Control
- Dataset management
- Monitor operations
- Dashboard management
- Infrastructure monitoring

</td>
<td width="50%">

### 🔒 Secure Execution
- Containerized environment
- Isolated execution
- API key authentication
- Environment variable support

</td>
</tr>
</table>

## 📋 Prerequisites

<table>
<tr>
<td width="120" align="center">
<img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="50"/>
<br/>Observe
</td>
<td>

- Observe account
- API key and Customer ID
- CLI access
- Appropriate permissions

</td>
</tr>
<tr>
<td width="120" align="center">
<img src="https://www.docker.com/wp-content/uploads/2023/08/logo-guide-logos-1.svg" width="50"/>
<br/>Docker
</td>
<td>

- Docker runtime
- Container access
- Volume mounts
- Network access

</td>
</tr>
</table>

## 🚀 Quick Start

### 1️⃣ Configure Observe Connection

```bash
export OBSERVE_API_KEY="your-api-key"
export OBSERVE_CUSTOMER_ID="your-customer-id"
export OBSERVE_DATASET_ID="your-dataset-id"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Observe CLI tools source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"datasets list"
"monitors list"
"dashboards list"
"resources list"
"events list"
```

## 📚 Available Commands

The Observe CLI wrapper supports all standard Observe CLI commands:

### Dataset Commands
- `datasets list` - List datasets
- `datasets show <dataset-id>` - Show dataset details
- `datasets create` - Create a new dataset
- `datasets update <dataset-id>` - Update a dataset
- `datasets delete <dataset-id>` - Delete a dataset

### Monitor Commands
- `monitors list` - List monitors
- `monitors show <monitor-id>` - Show monitor details
- `monitors create` - Create a new monitor
- `monitors update <monitor-id>` - Update a monitor
- `monitors delete <monitor-id>` - Delete a monitor

### Dashboard Commands
- `dashboards list` - List dashboards
- `dashboards show <dashboard-id>` - Show dashboard details
- `dashboards create` - Create a new dashboard
- `dashboards update <dashboard-id>` - Update a dashboard
- `dashboards delete <dashboard-id>` - Delete a dashboard

### Resource Commands
- `resources list` - List resources
- `resources show <resource-id>` - Show resource details
- `resources create` - Create a new resource
- `resources update <resource-id>` - Update a resource

### Event Commands
- `events list` - List events
- `events show <event-id>` - Show event details
- `events create` - Create a new event

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Observe Docs](https://img.shields.io/badge/Observe-Docs-00A3E0?style=for-the-badge&logo=observe)](https://docs.observeinc.com/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://slack.observeinc.com/)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="40" />

</div> 