# <img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="70" align="center" /> Datadog CLI Tools for Kubiya

<div align="center">

> 🚀 Direct Datadog CLI command execution through Kubiya

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Datadog](https://img.shields.io/badge/Datadog-Monitoring-632CA6?style=for-the-badge&logo=datadog&logoColor=white)](https://www.datadoghq.com/)
[![CLI](https://img.shields.io/badge/CLI-Powered-326CE5?style=for-the-badge&logo=terminal&logoColor=white)](https://docs.datadoghq.com/cli/)

</div>

## 🎯 Overview

This module provides a direct CLI wrapper for Datadog commands through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, this tool enables direct execution of any Datadog CLI command with full access to all Datadog features and capabilities.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#632CA6', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|CLI Command| B[Datadog CLI]
    B -->|Execute| C[Any Datadog Command]
    B -->|Return| D[Command Output]
    
    style A fill:#632CA6,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#632CA6,color:#fff,stroke-width:2px
    style D fill:#632CA6,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🔧 Universal CLI Access
- Execute any Datadog CLI command
- Full command-line functionality
- Direct access to all features
- Real-time command execution

</td>
<td width="50%">

### 🚀 Seamless Integration
- Native Datadog CLI experience
- Command validation
- Error handling
- Output formatting

</td>
</tr>
<tr>
<td width="50%">

### 📊 Complete Control
- Monitor management
- Dashboard operations
- Log management
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
<img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="50"/>
<br/>Datadog
</td>
<td>

- Datadog account
- API key and Application key
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

### 1️⃣ Configure Datadog Connection

```bash
export DD_API_KEY="your-api-key"
export DD_APP_KEY="your-application-key"
export DD_SITE="datadoghq.com"
```

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Datadog CLI tools source
4. Configure credentials

### 3️⃣ Start Using

#### Using Specialized Tools

**List all active metrics:**
```
datadog_list_metrics --mode active
```

**Search for specific metrics:**
```
datadog_list_metrics --mode search --query "system.cpu"
```

**List metrics with filtering:**
```
datadog_list_metrics --mode active --name_filter "cpu" --hours 6
```

**List metric namespaces:**
```
datadog_list_metrics --mode namespaces
```

#### Using Standard CLI Commands

Example commands:
```
"monitor list"
"dashboard list"
"logs list"
"host list"
"service list"
```

## 🛠️ Available Tools

This module provides several specialized tools for Datadog operations:

### 📊 Metrics Management
- **`datadog_list_metrics`** - Comprehensive metrics listing with filtering and grouping
  - List active metrics from the last N hours
  - Search metrics by name pattern
  - Filter by tags and namespaces
  - Group metrics by prefixes for better organization
  - Detailed metric metadata and information

### 📈 Monitor Management  
- **`datadog_list_monitors`** - List Datadog monitors with intelligent filtering
  - Filter by monitor states (alert, warn, no_data)
  - Search by monitor name
  - Filter by scope tags and monitor tags
  - Timeout protection for large datasets

### 🔍 Metrics Search & Query
- **`datadog_search_metrics`** - Search and query Datadog metrics using the API
  - Search for metrics by name/pattern
  - Query timeseries data for specific metrics
  - List active metrics from specified time ranges
  - Support for complex metric queries with tags

## 📚 Available Commands

The Datadog CLI wrapper also supports all standard Datadog CLI commands:

### Monitor Commands
- `monitor list` - List monitors
- `monitor show <monitor-id>` - Show monitor details
- `monitor create` - Create a new monitor
- `monitor update <monitor-id>` - Update a monitor
- `monitor delete <monitor-id>` - Delete a monitor

### Dashboard Commands
- `dashboard list` - List dashboards
- `dashboard show <dashboard-id>` - Show dashboard details
- `dashboard create` - Create a new dashboard
- `dashboard update <dashboard-id>` - Update a dashboard
- `dashboard delete <dashboard-id>` - Delete a dashboard

### Log Commands
- `logs list` - List log pipelines
- `logs show <pipeline-id>` - Show pipeline details
- `logs create` - Create a new pipeline
- `logs update <pipeline-id>` - Update a pipeline

### Host Commands
- `host list` - List hosts
- `host show <host-id>` - Show host details
- `host mute <host-id>` - Mute a host
- `host unmute <host-id>` - Unmute a host

### Service Commands
- `service list` - List services
- `service show <service-name>` - Show service details

## 📚 Learn More

<table>
<tr>
<td width="33%" align="center">

[![Kubiya Docs](https://img.shields.io/badge/Kubiya-Docs-blue?style=for-the-badge&logo=readthedocs)](https://docs.kubiya.ai)

</td>
<td width="33%" align="center">

[![Datadog Docs](https://img.shields.io/badge/Datadog-Docs-632CA6?style=for-the-badge&logo=datadog)](https://docs.datadoghq.com/)

</td>
<td width="33%" align="center">

[![Community](https://img.shields.io/badge/Join-Community-orange?style=for-the-badge&logo=slack)](https://chat.datadoghq.com/)

</td>
</tr>
</table>

---

<div align="center">

Built with ❤️ by the [Kubiya Community](https://chat.kubiya.ai)

<img src="https://cdn.worldvectorlogo.com/logos/datadog.svg" width="40" />

</div> 