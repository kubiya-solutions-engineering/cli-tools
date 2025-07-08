# <img src="https://cdn.worldvectorlogo.com/logos/observe.svg" width="70" align="center" /> Observe API Wrapper for Kubiya

<div align="center">

> 🚀 Direct Observe API operations through Kubiya using curl

[![Kubiya Platform](https://img.shields.io/badge/Kubiya-Platform-blue?style=for-the-badge&logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAADASURBVHgBjZLBDcIwEARPCX/cAakg6YB0QEqgA6ACQgWEDkgHpAPoAFcAJUAFrGYtWbKwlGQ/Zn1n786SyZxzEfYKd4uphSunA1rX7dKAzlWQBqbB+bacc1m4wCtFg1GM4RQKLRQXeKNh4Vz/lWjBHw3X+2KmE0+oB+71M0UR1WOwHvzJ0sDgC9xh0lbOLNbk4kUBJXw8ITPU4N+rR7zQwOKXvNDgvP6GpgbOXIQRX+4ZlX4QBPbBxbpV/FV8ARfDSCg/4aaZAAAAAElFTkSuQmCC)](https://chat.kubiya.ai)
[![Observe](https://img.shields.io/badge/Observe-Monitoring-00A3E0?style=for-the-badge&logo=observe&logoColor=white)](https://www.observeinc.com/)
[![API](https://img.shields.io/badge/API-Powered-326CE5?style=for-the-badge&logo=curl&logoColor=white)](https://docs.observeinc.com/)

</div>

## 🎯 Overview

This module provides a direct API wrapper for Observe operations through Kubiya. Built on Docker containers and leveraging the power of the Kubiya platform, this tool enables direct execution of any Observe API operation with full access to all Observe features and capabilities using simple curl commands.

## 🏗️ How It Works

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#00A3E0', 'fontFamily': 'arial', 'fontSize': '16px' }}}%%
graph LR
    A([Kubiya<br/>Teammate]) -->|API Command| B[Observe API Wrapper]
    B -->|curl| C[Observe API]
    B -->|Return| D[Formatted Response]
    
    style A fill:#00A3E0,color:#fff,stroke-width:2px
    style B fill:#1a73e8,color:#fff,stroke-width:2px
    style C fill:#00A3E0,color:#fff,stroke-width:2px
    style D fill:#00A3E0,color:#fff,stroke-width:2px
```

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🔧 Universal API Access
- Execute any Observe API operation
- Full API functionality
- Direct access to all endpoints
- Real-time API execution

</td>
<td width="50%">

### 🚀 Seamless Integration
- Native API experience
- Command validation
- Error handling
- JSON response formatting

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
- API access
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
export OBSERVE_API_KEY="your-api-token"
export OBSERVE_CUSTOMER_ID="your-customer-id"
export OBSERVE_DATASET_ID="your-dataset-id"
```

**Note:** The API uses Bearer token authentication with the format: `Authorization: Bearer <customerid> <token>`

### 2️⃣ Install Tools

1. Visit [chat.kubiya.ai](https://chat.kubiya.ai)
2. Navigate to teammate settings
3. Install Observe API wrapper source
4. Configure credentials

### 3️⃣ Start Using

Example commands:
```
"datasets list"
"monitors list"
"dashboards list"
"resources list"
"events list"
"query <dataset-id> <oql-query>"
"api GET /v1/datasets"
```

## 📚 Available Commands

The Observe API wrapper supports all standard Observe API operations:

### Dataset Commands
- `datasets list` - List all datasets
- `datasets show <dataset-id>` - Show dataset details

### Monitor Commands
- `monitors list` - List all monitors
- `monitors show <monitor-id>` - Show monitor details

### Dashboard Commands
- `dashboards list` - List all dashboards
- `dashboards show <dashboard-id>` - Show dashboard details

### Resource Commands
- `resources list` - List all resources
- `resources show <resource-id>` - Show resource details

### Event Commands
- `events list` - List all events
- `events show <event-id>` - Show event details

### Query Commands
- `query <dataset-id> <oql-query>` - Execute OQL query on dataset
- `advanced-query <dataset-id> [options]` - Advanced query with filters, time ranges, and parameters

### Custom API Commands
- `api <method> <endpoint> [query-params] [body]` - Custom API call

## 🔧 Command Examples

### Basic Operations
```bash
# List all datasets
"datasets list"

# Show specific dataset
"datasets show your-dataset-id"

# List monitors
"monitors list"

# Show specific monitor
"monitors show your-monitor-id"
```

### Query Operations
```bash
# Execute OQL query
"query your-dataset-id 'pick_col timestamp, log | limit 10'"

# Complex query
"query your-dataset-id 'filter severity == \"error\" | pick_col timestamp, message, severity | limit 50'"
```

### Advanced Query Operations
```bash
# Query with time preset
"advanced-query your-dataset-id --time-preset PAST_1_HOUR"

# Query with specific time range
"advanced-query your-dataset-id --time-start 1686165391864 --time-end 1686251791864"

# Query with filter
"advanced-query your-dataset-id --filter-eq status error"

# Query with operator filter
"advanced-query your-dataset-id --filter severity != warning"

# Query with OPAL statement
"advanced-query your-dataset-id --opal 'filter severity == \"error\"'"

# Query with multiple parameters
"advanced-query your-dataset-id --time-preset PAST_15_MINUTES --filter-eq level ERROR --param environment production"
```

### Custom API Calls
```bash
# GET request
"api GET /v1/datasets"

# GET with query parameters
"api GET /v1/datasets 'limit=10&offset=0'"

# POST request with body
"api POST /v1/query '{\"query\": \"pick_col timestamp, log | limit 10\", \"dataset\": \"your-dataset-id\"}'"

# PUT request
"api PUT /v1/datasets/your-dataset-id '{\"name\": \"Updated Dataset\"}'"

# DELETE request
"api DELETE /v1/monitors/your-monitor-id"
```

## 📊 Advanced URL Parameters

The API wrapper supports all Observe URL parameters for advanced filtering and customization:

### Time Ranges
- `--time-start <timestamp>` - Start time (Unix epoch or ISO 8601)
- `--time-end <timestamp>` - End time (Unix epoch or ISO 8601)  
- `--time-preset <preset>` - Time preset (TODAY, YESTERDAY, PAST_1_HOUR, etc.)

### Filters
- `--filter-eq <column> <value>` - Simple equals filter
- `--filter <column> <operator> <value>` - Advanced filter with operators (=, !=, ~, !~, >, <, >=, <=)

### OPAL Statements
- `--opal <opal-statement>` - Full OPAL statement for complex filtering

### Parameters
- `--param <key> <value>` - Custom parameters for dashboards and worksheets
- `--tab <tab-name>` - Tab selection (resources, logs, related)
- `--dash <dashboard-id>` - Dashboard selection

### Supported Time Presets
- TODAY, YESTERDAY, THIS_DAY_LAST_WEEK
- LAST_WEEK, LAST_MONTH
- PAST_5_MINUTES, PAST_10_MINUTES, PAST_15_MINUTES, PAST_30_MINUTES
- PAST_60_MINUTES, PAST_2_HOURS, PAST_4_HOURS, PAST_6_HOURS
- PAST_12_HOURS, PAST_24_HOURS
- PAST_2_DAYS, PAST_3_DAYS, PAST_4_DAYS, PAST_7_DAYS, PAST_14_DAYS, PAST_30_DAYS

## 📊 Response Format

All API responses include:
- **HTTP Status Code** - Success/error indication
- **Response Time** - Execution duration
- **Formatted JSON** - Pretty-printed response data
- **Error Handling** - Clear error messages

Example response:
```
=== Observe API Operation ===
Command: datasets list
Operation: datasets
Sub-operation: list
Base URL: https://your-customer-id.observeinc.com

Listing datasets...

=== Response ===
HTTP Status: 200
Response Time: 0.5s

✅ Success (200)

{
  "datasets": [
    {
      "id": "dataset-1",
      "name": "Container Logs",
      "description": "Kubernetes container logs"
    }
  ]
}
```

## 🔒 Security

- **API Key Authentication** - Bearer token authentication
- **Environment Variables** - Secure credential storage
- **Container Isolation** - Isolated execution environment
- **No CLI Installation** - No external binary dependencies

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