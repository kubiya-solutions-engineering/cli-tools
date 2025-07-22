from typing import List
import sys
from .base import ArgoCDCLITool, Arg
from kubiya_sdk.tools.registry import tool_registry

class CLITools:
    """High-performance ArgoCD API tools with intelligent caching and filtering."""

    def __init__(self):
        """Initialize and register ArgoCD API tools."""
        try:
            tools = [
                self.list_applications(),
                self.get_application(),
                self.list_clusters(),
                self.list_repositories(),
                self.application_sync(),
                self.application_history(),
                self.workspace_manager()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("argocd_cli", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register ArgoCD API wrapper tools: {str(e)}", file=sys.stderr)
            raise

    def list_applications(self) -> ArgoCDCLITool:
        """List ArgoCD applications with advanced filtering and caching."""
        return ArgoCDCLITool(
            name="argocd_list_applications",
            description="List ArgoCD applications with filtering, search, pagination, and multiple output formats. Supports project filtering, health status filtering, and sync status filtering.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate environment
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN and ARGOCD_SERVER are required"
                exit 1
            fi
            
            # Performance defaults and limits
            LIMIT=${limit:-50}
            OFFSET=${offset:-0}
            OUTPUT_FORMAT=${output_format:-"table"}
            REFRESH=${refresh:-"false"}
            
            echo "🚀 Fetching ArgoCD applications (limit: $LIMIT, offset: $OFFSET)..."
            
            # Check cache first unless refresh is requested
            mkdir -p "/workspace/argocd-data/cache"
            CACHE_KEY=$(echo "apps_${LIMIT}_${OFFSET}_${project_filter}_${health_filter}_${sync_filter}_$(date +%Y%m%d%H)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/argocd-data/cache/apps_${CACHE_KEY}.json"
            
            if [ "$REFRESH" != "true" ] && [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -15 | wc -l) -gt 0 ]; then
                echo "⚡ Using cached applications list from: apps_${CACHE_KEY}.json"
                RESPONSE=$(cat "$CACHE_FILE")
            else
                # Build query parameters
                QUERY_PARAMS=""
                if [ -n "$project_filter" ]; then
                    QUERY_PARAMS="${QUERY_PARAMS}projects=$project_filter&"
                fi
                
                # Clean up trailing &
                QUERY_PARAMS=$(echo "$QUERY_PARAMS" | sed 's/&$//')
                
                # Build URL
                URL="https://$ARGOCD_SERVER/api/v1/applications"
                if [ -n "$QUERY_PARAMS" ]; then
                    URL="$URL?$QUERY_PARAMS"
                fi
                
                # Execute API call with proper authentication
                RESPONSE=$(curl -s --max-time 30 --fail \
                    -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    -H "Content-Type: application/json" \
                    "$URL" 2>/dev/null)
                
                if [ $? -ne 0 ]; then
                    echo "❌ API request failed. Check ARGOCD_SERVER, ARGOCD_TOKEN, and network connectivity."
                    exit 1
                fi
                
                # Cache the response
                if [ -n "$RESPONSE" ]; then
                    echo "$RESPONSE" > "$CACHE_FILE"
                    echo "💾 Applications cached to workspace: argocd-data/cache/apps_${CACHE_KEY}.json"
                fi
            fi
            
            # Apply additional filtering if specified
            if [ -n "$health_filter" ] || [ -n "$sync_filter" ]; then
                echo "🔍 Applying additional filters..."
                FILTERED_RESPONSE="$RESPONSE"
                
                if [ -n "$health_filter" ]; then
                    FILTERED_RESPONSE=$(echo "$FILTERED_RESPONSE" | jq --arg health "$health_filter" '.items | map(select(.status.health.status == $health))')
                else
                    FILTERED_RESPONSE=$(echo "$FILTERED_RESPONSE" | jq '.items')
                fi
                
                if [ -n "$sync_filter" ]; then
                    FILTERED_RESPONSE=$(echo "$FILTERED_RESPONSE" | jq --arg sync "$sync_filter" 'map(select(.status.sync.status == $sync))')
                fi
                
                # Reconstruct response format
                RESPONSE=$(echo "$FILTERED_RESPONSE" | jq '{items: .}')
            fi
            
            # Apply pagination to results
            if echo "$RESPONSE" | jq -e '.items' >/dev/null 2>&1; then
                TOTAL_COUNT=$(echo "$RESPONSE" | jq '.items | length')
                echo "📊 Found $TOTAL_COUNT applications"
                
                # Apply limit and offset
                PAGINATED_RESPONSE=$(echo "$RESPONSE" | jq --argjson limit "$LIMIT" --argjson offset "$OFFSET" '.items | .[$offset:$offset+$limit]')
            else
                echo "⚠️ Unexpected response format"
                PAGINATED_RESPONSE="[]"
            fi
            
            # Format output based on requested format
            case "$OUTPUT_FORMAT" in
                "table")
                    echo "$PAGINATED_RESPONSE" | jq -r '
                        if length > 0 then
                            (["NAME", "PROJECT", "CLUSTER", "NAMESPACE", "HEALTH", "SYNC", "SOURCE"] | @csv),
                            (.[] | [
                                .metadata.name,
                                (.spec.project // "default"),
                                (.spec.destination.server // .spec.destination.name // "unknown"),
                                (.spec.destination.namespace // "default"),
                                (.status.health.status // "unknown"),
                                (.status.sync.status // "unknown"),
                                (.spec.source.repoURL // "unknown")
                            ] | @csv)
                        else
                            "No applications found"
                        end' | column -t -s ','
                    ;;
                "json")
                    echo "$PAGINATED_RESPONSE" | jq '.'
                    ;;
                "compact")
                    echo "$PAGINATED_RESPONSE" | jq -r '.[] | "\\(.metadata.name): \\(.status.health.status // "unknown")/\\(.status.sync.status // "unknown") in \\(.spec.destination.namespace // "default")"'
                    ;;
                "summary")
                    echo "$PAGINATED_RESPONSE" | jq -r '
                        "Total applications: " + (length | tostring) + "\\n" +
                        "Health status breakdown:" +
                        (group_by(.status.health.status) | map("  \\(.[0].status.health.status // "unknown"): \\(length)") | join("\\n")) + "\\n" +
                        "Sync status breakdown:" +
                        (group_by(.status.sync.status) | map("  \\(.[0].status.sync.status // "unknown"): \\(length)") | join("\\n"))'
                    ;;
                *)
                    echo "$PAGINATED_RESPONSE" | jq '.'
                    ;;
            esac
            """,
            args=[
                Arg(name="limit", description="Maximum number of applications to return (default: 50)", required=False),
                Arg(name="offset", description="Number of applications to skip for pagination (default: 0)", required=False),
                Arg(name="project_filter", description="Filter by project name", required=False),
                Arg(name="health_filter", description="Filter by health status: Healthy, Progressing, Degraded, Suspended, Missing, Unknown", required=False),
                Arg(name="sync_filter", description="Filter by sync status: Synced, OutOfSync, Unknown", required=False),
                Arg(name="output_format", description="Output format: table, json, compact, summary (default: table)", required=False),
                Arg(name="refresh", description="Force refresh cache: true/false (default: false)", required=False)
            ],
            image="alpine:latest"
        )

    def get_application(self) -> ArgoCDCLITool:
        """Get detailed information about a specific ArgoCD application."""
        return ArgoCDCLITool(
            name="argocd_get_application",
            description="Get detailed information about a specific ArgoCD application including resources, history, and manifests. Supports caching and multiple output formats.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate inputs
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ] || [ -z "$app_name" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN, ARGOCD_SERVER, and app_name are required"
                exit 1
            fi
            
            OUTPUT_FORMAT=${output_format:-"detailed"}
            REFRESH=${refresh:-"false"}
            INCLUDE_RESOURCES=${include_resources:-"true"}
            
            echo "🔍 Fetching application: $app_name"
            
            # Check cache first
            mkdir -p "/workspace/argocd-data/cache"
            CACHE_KEY=$(echo "app_${app_name}_$(date +%Y%m%d%H%M)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/argocd-data/cache/app_${CACHE_KEY}.json"
            
            if [ "$REFRESH" != "true" ] && [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -10 | wc -l) -gt 0 ]; then
                echo "⚡ Using cached application data from: app_${CACHE_KEY}.json"
                APP_DATA=$(cat "$CACHE_FILE")
            else
                # Fetch application details
                APP_DATA=$(curl -s --max-time 30 --fail \
                    -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    -H "Content-Type: application/json" \
                    "https://$ARGOCD_SERVER/api/v1/applications/$app_name" 2>/dev/null)
                
                if [ $? -ne 0 ]; then
                    echo "❌ Failed to fetch application $app_name. Check application name and permissions."
                    exit 1
                fi
                
                # Cache the response
                if [ -n "$APP_DATA" ]; then
                    echo "$APP_DATA" > "$CACHE_FILE"
                    echo "💾 Application data cached to workspace: argocd-data/cache/app_${CACHE_KEY}.json"
                fi
            fi
            
            # Fetch resources if requested
            if [ "$INCLUDE_RESOURCES" = "true" ]; then
                RESOURCES_CACHE="/workspace/argocd-data/cache/resources_${CACHE_KEY}.json"
                
                if [ "$REFRESH" != "true" ] && [ -f "$RESOURCES_CACHE" ] && [ $(find "$RESOURCES_CACHE" -mmin -10 | wc -l) -gt 0 ]; then
                    RESOURCES_DATA=$(cat "$RESOURCES_CACHE")
                else
                    RESOURCES_DATA=$(curl -s --max-time 30 --fail \
                        -H "Authorization: Bearer $ARGOCD_TOKEN" \
                        -H "Content-Type: application/json" \
                        "https://$ARGOCD_SERVER/api/v1/applications/$app_name/resource-tree" 2>/dev/null)
                    
                    if [ $? -eq 0 ] && [ -n "$RESOURCES_DATA" ]; then
                        echo "$RESOURCES_DATA" > "$RESOURCES_CACHE"
                    fi
                fi
            fi
            
            # Format output
            case "$OUTPUT_FORMAT" in
                "basic")
                    echo "$APP_DATA" | jq -r '
                        "Application: " + .metadata.name + "\\n" +
                        "Project: " + (.spec.project // "default") + "\\n" +
                        "Cluster: " + (.spec.destination.server // .spec.destination.name // "unknown") + "\\n" +
                        "Namespace: " + (.spec.destination.namespace // "default") + "\\n" +
                        "Health: " + (.status.health.status // "unknown") + "\\n" +
                        "Sync: " + (.status.sync.status // "unknown") + "\\n" +
                        "Source: " + (.spec.source.repoURL // "unknown") + "\\n" +
                        "Path: " + (.spec.source.path // ".")'
                    ;;
                "detailed")
                    echo "📱 Application Details:"
                    echo "====================="
                    echo "$APP_DATA" | jq -r '
                        "Name: " + .metadata.name,
                        "Project: " + (.spec.project // "default"),
                        "Created: " + (.metadata.creationTimestamp // "unknown"),
                        "",
                        "🎯 Destination:",
                        "  Cluster: " + (.spec.destination.server // .spec.destination.name // "unknown"),
                        "  Namespace: " + (.spec.destination.namespace // "default"),
                        "",
                        "📦 Source:",
                        "  Repository: " + (.spec.source.repoURL // "unknown"),
                        "  Path: " + (.spec.source.path // "."),
                        "  Branch/Tag: " + (.spec.source.targetRevision // "HEAD"),
                        "",
                        "🏥 Health Status: " + (.status.health.status // "unknown"),
                        "🔄 Sync Status: " + (.status.sync.status // "unknown")'
                    
                    if [ "$INCLUDE_RESOURCES" = "true" ] && [ -n "$RESOURCES_DATA" ]; then
                        echo ""
                        echo "📋 Resources:"
                        echo "$RESOURCES_DATA" | jq -r '.nodes[]? | "  • \\(.kind)/\\(.name) - \\(.health // "unknown")"' | head -20
                        
                        TOTAL_RESOURCES=$(echo "$RESOURCES_DATA" | jq -r '.nodes | length // 0')
                        if [ "$TOTAL_RESOURCES" -gt 20 ]; then
                            echo "  ... and $((TOTAL_RESOURCES - 20)) more resources"
                        fi
                    fi
                    ;;
                "json")
                    if [ "$INCLUDE_RESOURCES" = "true" ] && [ -n "$RESOURCES_DATA" ]; then
                        jq -n --argjson app "$APP_DATA" --argjson resources "$RESOURCES_DATA" '{application: $app, resources: $resources}'
                    else
                        echo "$APP_DATA" | jq '.'
                    fi
                    ;;
                "resources")
                    if [ -n "$RESOURCES_DATA" ]; then
                        echo "📋 Application Resources:"
                        echo "========================"
                        echo "$RESOURCES_DATA" | jq -r '.nodes[]? | "\\(.kind)/\\(.name) - Health: \\(.health // "unknown"), Sync: \\(.status // "unknown")"'
                    else
                        echo "No resource data available"
                    fi
                    ;;
                *)
                    echo "$APP_DATA" | jq '.'
                    ;;
            esac
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="output_format", description="Output format: basic, detailed, json, resources (default: detailed)", required=False),
                Arg(name="include_resources", description="Include resource tree information: true/false (default: true)", required=False),
                Arg(name="refresh", description="Force refresh cache: true/false (default: false)", required=False)
            ],
            image="alpine:latest"
        )

    def list_clusters(self) -> ArgoCDCLITool:
        """List ArgoCD clusters with health status and connection info."""
        return ArgoCDCLITool(
            name="argocd_list_clusters",
            description="List all ArgoCD clusters with health status, connection info, and filtering capabilities. Supports caching and multiple output formats.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate environment
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN and ARGOCD_SERVER are required"
                exit 1
            fi
            
            OUTPUT_FORMAT=${output_format:-"table"}
            REFRESH=${refresh:-"false"}
            
            echo "🌐 Fetching ArgoCD clusters..."
            
            # Check cache first
            mkdir -p "/workspace/argocd-data/cache"
            CACHE_KEY=$(echo "clusters_$(date +%Y%m%d%H)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/argocd-data/cache/clusters_${CACHE_KEY}.json"
            
            if [ "$REFRESH" != "true" ] && [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -30 | wc -l) -gt 0 ]; then
                echo "⚡ Using cached clusters list from: clusters_${CACHE_KEY}.json"
                RESPONSE=$(cat "$CACHE_FILE")
            else
                # Execute API call
                RESPONSE=$(curl -s --max-time 30 --fail \
                    -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    -H "Content-Type: application/json" \
                    "https://$ARGOCD_SERVER/api/v1/clusters" 2>/dev/null)
                
                if [ $? -ne 0 ]; then
                    echo "❌ API request failed. Check ARGOCD_SERVER, ARGOCD_TOKEN, and permissions."
                    exit 1
                fi
                
                # Cache the response
                if [ -n "$RESPONSE" ]; then
                    echo "$RESPONSE" > "$CACHE_FILE"
                    echo "💾 Clusters cached to workspace: argocd-data/cache/clusters_${CACHE_KEY}.json"
                fi
            fi
            
            # Format output
            case "$OUTPUT_FORMAT" in
                "table")
                    echo "$RESPONSE" | jq -r '
                        if .items and (.items | length > 0) then
                            (["NAME", "SERVER", "VERSION", "STATUS", "MESSAGE"] | @csv),
                            (.items[] | [
                                (.name // "in-cluster"),
                                .server,
                                (.serverVersion // "unknown"),
                                (.connectionState.status // "unknown"),
                                (.connectionState.message // "")
                            ] | @csv)
                        else
                            "No clusters found"
                        end' | column -t -s ','
                    ;;
                "json")
                    echo "$RESPONSE" | jq '.'
                    ;;
                "summary")
                    echo "$RESPONSE" | jq -r '
                        if .items then
                            "Total clusters: " + (.items | length | tostring) + "\\n" +
                            "Connection status:" +
                            (.items | group_by(.connectionState.status) | map("  \\(.[0].connectionState.status // "unknown"): \\(length)") | join("\\n"))
                        else
                            "No clusters found"
                        end'
                    ;;
                *)
                    echo "$RESPONSE" | jq '.'
                    ;;
            esac
            """,
            args=[
                Arg(name="output_format", description="Output format: table, json, summary (default: table)", required=False),
                Arg(name="refresh", description="Force refresh cache: true/false (default: false)", required=False)
            ],
            image="alpine:latest"
        )

    def list_repositories(self) -> ArgoCDCLITool:
        """List ArgoCD repositories with connection status."""
        return ArgoCDCLITool(
            name="argocd_list_repositories",
            description="List all ArgoCD repositories with connection status, credentials info, and filtering. Supports caching and multiple output formats.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate environment
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN and ARGOCD_SERVER are required"
                exit 1
            fi
            
            OUTPUT_FORMAT=${output_format:-"table"}
            REFRESH=${refresh:-"false"}
            REPO_TYPE=${repo_type:-"all"}
            
            echo "📦 Fetching ArgoCD repositories..."
            
            # Check cache first
            mkdir -p "/workspace/argocd-data/cache"
            CACHE_KEY=$(echo "repos_${REPO_TYPE}_$(date +%Y%m%d%H)" | md5sum | cut -d' ' -f1)
            CACHE_FILE="/workspace/argocd-data/cache/repos_${CACHE_KEY}.json"
            
            if [ "$REFRESH" != "true" ] && [ -f "$CACHE_FILE" ] && [ $(find "$CACHE_FILE" -mmin -30 | wc -l) -gt 0 ]; then
                echo "⚡ Using cached repositories list from: repos_${CACHE_KEY}.json"
                RESPONSE=$(cat "$CACHE_FILE")
            else
                # Execute API call
                RESPONSE=$(curl -s --max-time 30 --fail \
                    -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    -H "Content-Type: application/json" \
                    "https://$ARGOCD_SERVER/api/v1/repositories" 2>/dev/null)
                
                if [ $? -ne 0 ]; then
                    echo "❌ API request failed. Check ARGOCD_SERVER, ARGOCD_TOKEN, and permissions."
                    exit 1
                fi
                
                # Cache the response
                if [ -n "$RESPONSE" ]; then
                    echo "$RESPONSE" > "$CACHE_FILE"
                    echo "💾 Repositories cached to workspace: argocd-data/cache/repos_${CACHE_KEY}.json"
                fi
            fi
            
            # Apply type filtering
            if [ "$REPO_TYPE" != "all" ]; then
                FILTERED_RESPONSE=$(echo "$RESPONSE" | jq --arg type "$REPO_TYPE" '.items | map(select(.type == $type))')
                RESPONSE=$(echo "$FILTERED_RESPONSE" | jq '{items: .}')
            fi
            
            # Format output
            case "$OUTPUT_FORMAT" in
                "table")
                    echo "$RESPONSE" | jq -r '
                        if .items and (.items | length > 0) then
                            (["REPOSITORY", "TYPE", "STATUS", "PROJECT", "INSECURE"] | @csv),
                            (.items[] | [
                                .repo,
                                (.type // "git"),
                                (.connectionState.status // "unknown"),
                                (.project // "default"),
                                (.insecure // false | tostring)
                            ] | @csv)
                        else
                            "No repositories found"
                        end' | column -t -s ','
                    ;;
                "json")
                    echo "$RESPONSE" | jq '.'
                    ;;
                "summary")
                    echo "$RESPONSE" | jq -r '
                        if .items then
                            "Total repositories: " + (.items | length | tostring) + "\\n" +
                            "Repository types:" +
                            (.items | group_by(.type // "git") | map("  \\(.[0].type // "git"): \\(length)") | join("\\n")) + "\\n" +
                            "Connection status:" +
                            (.items | group_by(.connectionState.status) | map("  \\(.[0].connectionState.status // "unknown"): \\(length)") | join("\\n"))
                        else
                            "No repositories found"
                        end'
                    ;;
                *)
                    echo "$RESPONSE" | jq '.'
                    ;;
            esac
            """,
            args=[
                Arg(name="repo_type", description="Filter by repository type: git, helm, all (default: all)", required=False),
                Arg(name="output_format", description="Output format: table, json, summary (default: table)", required=False),
                Arg(name="refresh", description="Force refresh cache: true/false (default: false)", required=False)
            ],
            image="alpine:latest"
        )

    def application_sync(self) -> ArgoCDCLITool:
        """Sync an ArgoCD application with advanced options."""
        return ArgoCDCLITool(
            name="argocd_sync_application",
            description="Sync an ArgoCD application with options for dry-run, prune, force, and resource targeting. Monitors sync progress and provides detailed feedback.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate inputs
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ] || [ -z "$app_name" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN, ARGOCD_SERVER, and app_name are required"
                exit 1
            fi
            
            DRY_RUN=${dry_run:-"false"}
            PRUNE=${prune:-"false"}
            FORCE=${force:-"false"}
            WAIT_FOR_COMPLETION=${wait:-"true"}
            
            echo "🔄 Initiating sync for application: $app_name"
            
            # Build sync request payload
            SYNC_PAYLOAD=$(jq -n \
                --argjson dryRun "$(echo $DRY_RUN | tr '[:upper:]' '[:lower:]')" \
                --argjson prune "$(echo $PRUNE | tr '[:upper:]' '[:lower:]')" \
                --argjson force "$(echo $FORCE | tr '[:upper:]' '[:lower:]')" \
                '{
                    dryRun: $dryRun,
                    prune: $prune,
                    force: $force
                }')
            
            # Add specific resources if provided
            if [ -n "$resources" ]; then
                RESOURCES_ARRAY=$(echo "$resources" | jq -R 'split(",") | map({group: "", version: "v1", kind: split("/")[0], name: split("/")[1]})')
                SYNC_PAYLOAD=$(echo "$SYNC_PAYLOAD" | jq --argjson resources "$RESOURCES_ARRAY" '. + {resources: $resources}')
            fi
            
            echo "📋 Sync options:"
            echo "  Dry run: $DRY_RUN"
            echo "  Prune: $PRUNE"
            echo "  Force: $FORCE"
            if [ -n "$resources" ]; then
                echo "  Target resources: $resources"
            fi
            echo ""
            
            # Execute sync
            SYNC_RESPONSE=$(curl -s --max-time 60 --fail \
                -X POST \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                -H "Content-Type: application/json" \
                -d "$SYNC_PAYLOAD" \
                "https://$ARGOCD_SERVER/api/v1/applications/$app_name/sync" 2>/dev/null)
            
            if [ $? -ne 0 ]; then
                echo "❌ Sync request failed. Check application name, permissions, and server connectivity."
                exit 1
            fi
            
            # Parse response
            if echo "$SYNC_RESPONSE" | jq -e '.metadata' >/dev/null 2>&1; then
                OPERATION_NAME=$(echo "$SYNC_RESPONSE" | jq -r '.metadata.name')
                echo "✅ Sync initiated successfully"
                echo "🆔 Operation: $OPERATION_NAME"
                
                if [ "$DRY_RUN" = "true" ]; then
                    echo ""
                    echo "🧪 Dry Run Results:"
                    echo "$SYNC_RESPONSE" | jq -r '.status.message // "Sync would be performed"'
                    exit 0
                fi
                
                # Wait for completion if requested
                if [ "$WAIT_FOR_COMPLETION" = "true" ]; then
                    echo ""
                    echo "⏳ Waiting for sync to complete..."
                    
                    for i in $(seq 1 60); do
                        sleep 5
                        
                        # Check operation status
                        OP_STATUS=$(curl -s --max-time 10 --fail \
                            -H "Authorization: Bearer $ARGOCD_TOKEN" \
                            "https://$ARGOCD_SERVER/api/v1/applications/$app_name/operation" 2>/dev/null)
                        
                        if [ $? -ne 0 ] || [ -z "$OP_STATUS" ]; then
                            echo "✅ Sync completed (no active operation)"
                            break
                        fi
                        
                        PHASE=$(echo "$OP_STATUS" | jq -r '.operation.sync.phase // "unknown"')
                        MESSAGE=$(echo "$OP_STATUS" | jq -r '.operation.sync.message // ""')
                        
                        echo "⏳ Status: $PHASE - $MESSAGE"
                        
                        if [ "$PHASE" = "Succeeded" ]; then
                            echo "✅ Sync completed successfully!"
                            break
                        elif [ "$PHASE" = "Failed" ] || [ "$PHASE" = "Error" ]; then
                            echo "❌ Sync failed: $MESSAGE"
                            echo "$OP_STATUS" | jq -r '.operation.sync.result // "No detailed error available"'
                            exit 1
                        fi
                    done
                fi
                
                # Show final application status
                echo ""
                echo "📱 Final Application Status:"
                APP_STATUS=$(curl -s --max-time 10 --fail \
                    -H "Authorization: Bearer $ARGOCD_TOKEN" \
                    "https://$ARGOCD_SERVER/api/v1/applications/$app_name" 2>/dev/null)
                
                if [ $? -eq 0 ] && [ -n "$APP_STATUS" ]; then
                    echo "$APP_STATUS" | jq -r '
                        "  Health: " + (.status.health.status // "unknown") + "\\n" +
                        "  Sync: " + (.status.sync.status // "unknown") + "\\n" +
                        "  Last Sync: " + (.status.operationState.finishedAt // "unknown")'
                fi
                
            else
                echo "❌ Unexpected response format:"
                echo "$SYNC_RESPONSE" | jq '.'
                exit 1
            fi
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application to sync", required=True),
                Arg(name="dry_run", description="Perform a dry run without making changes: true/false (default: false)", required=False),
                Arg(name="prune", description="Prune resources not defined in Git: true/false (default: false)", required=False),
                Arg(name="force", description="Force sync even if application is out of sync: true/false (default: false)", required=False),
                Arg(name="resources", description="Comma-separated list of specific resources to sync (format: Kind/Name)", required=False),
                Arg(name="wait", description="Wait for sync completion: true/false (default: true)", required=False)
            ],
            image="alpine:latest"
        )

    def application_history(self) -> ArgoCDCLITool:
        """Get ArgoCD application deployment history and rollback options."""
        return ArgoCDCLITool(
            name="argocd_application_history",
            description="Get ArgoCD application deployment history with detailed revision information. Supports rollback operations and history analysis.",
            content="""
            # Install required tools
            if ! command -v curl >/dev/null 2>&1; then apk add --no-cache curl; fi
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            # Validate inputs
            if [ -z "$ARGOCD_TOKEN" ] || [ -z "$ARGOCD_SERVER" ] || [ -z "$app_name" ]; then
                echo "❌ Missing required parameters: ARGOCD_TOKEN, ARGOCD_SERVER, and app_name are required"
                exit 1
            fi
            
            LIMIT=${limit:-10}
            ACTION=${action:-"history"}
            OUTPUT_FORMAT=${output_format:-"table"}
            
            echo "📚 Fetching deployment history for: $app_name"
            
            # Get application history
            HISTORY_RESPONSE=$(curl -s --max-time 30 --fail \
                -H "Authorization: Bearer $ARGOCD_TOKEN" \
                "https://$ARGOCD_SERVER/api/v1/applications/$app_name/revisions" 2>/dev/null)
            
            if [ $? -ne 0 ]; then
                echo "❌ Failed to fetch application history. Check application name and permissions."
                exit 1
            fi
            
            case "$ACTION" in
                "history"|"list")
                    case "$OUTPUT_FORMAT" in
                        "table")
                            echo "$HISTORY_RESPONSE" | jq -r --argjson limit "$LIMIT" '
                                if length > 0 then
                                    (["REVISION", "DATE", "AUTHOR", "MESSAGE"] | @csv),
                                    (.[:$limit][] | [
                                        (.revision // "unknown"),
                                        (.deployedAt // .date // "unknown"),
                                        (.author // "unknown"),
                                        ((.message // "") | gsub("\\n"; " ") | .[0:50])
                                    ] | @csv)
                                else
                                    "No history found"
                                end' | column -t -s ','
                            ;;
                        "json")
                            echo "$HISTORY_RESPONSE" | jq --argjson limit "$LIMIT" '.[:$limit]'
                            ;;
                        "summary")
                            echo "$HISTORY_RESPONSE" | jq -r --argjson limit "$LIMIT" '
                                if length > 0 then
                                    "Total revisions: " + (length | tostring) + "\\n" +
                                    "Showing last " + ($limit | tostring) + " revisions:\\n" +
                                    (.[:$limit][] | "  " + (.revision // "unknown") + " - " + (.deployedAt // .date // "unknown") + " by " + (.author // "unknown"))
                                else
                                    "No history found"
                                end'
                            ;;
                    esac
                    ;;
                "rollback")
                    if [ -z "$revision" ]; then
                        echo "❌ Revision parameter required for rollback action"
                        exit 1
                    fi
                    
                    echo "🔄 Rolling back to revision: $revision"
                    
                    # Perform rollback by syncing to specific revision
                    ROLLBACK_PAYLOAD=$(jq -n \
                        --arg revision "$revision" \
                        '{
                            revision: $revision,
                            prune: false,
                            dryRun: false
                        }')
                    
                    ROLLBACK_RESPONSE=$(curl -s --max-time 60 --fail \
                        -X POST \
                        -H "Authorization: Bearer $ARGOCD_TOKEN" \
                        -H "Content-Type: application/json" \
                        -d "$ROLLBACK_PAYLOAD" \
                        "https://$ARGOCD_SERVER/api/v1/applications/$app_name/sync" 2>/dev/null)
                    
                    if [ $? -ne 0 ]; then
                        echo "❌ Rollback failed. Check revision and permissions."
                        exit 1
                    fi
                    
                    echo "✅ Rollback initiated to revision $revision"
                    echo "🆔 Operation: $(echo "$ROLLBACK_RESPONSE" | jq -r '.metadata.name // "unknown"')"
                    ;;
                *)
                    echo "❌ Unknown action: $ACTION"
                    echo "Available actions: history, list, rollback"
                    exit 1
                    ;;
            esac
            """,
            args=[
                Arg(name="app_name", description="Name of the ArgoCD application", required=True),
                Arg(name="action", description="Action to perform: history, list, rollback (default: history)", required=False),
                Arg(name="limit", description="Number of history entries to show (default: 10)", required=False),
                Arg(name="revision", description="Revision to rollback to (required for rollback action)", required=False),
                Arg(name="output_format", description="Output format: table, json, summary (default: table)", required=False)
            ],
            image="alpine:latest"
        )

    def workspace_manager(self) -> ArgoCDCLITool:
        """Manage ArgoCD workspace data including cache and cleanup operations."""
        return ArgoCDCLITool(
            name="argocd_workspace_manager",
            description="Manage ArgoCD workspace data including cache management, cleanup operations, and storage monitoring. View cached data and perform maintenance tasks.",
            content="""
            # Install dependencies
            if ! command -v jq >/dev/null 2>&1; then apk add --no-cache jq; fi
            
            ACTION=${action:-"status"}
            
            echo "🗂️  ArgoCD Workspace Manager"
            echo "==========================="
            echo "Workspace: /workspace/argocd-data"
            echo ""
            
            # Create directories if they don't exist
            mkdir -p "/workspace/argocd-data/cache"
            
            case "$ACTION" in
                "status"|"info")
                    echo "📊 Workspace Status:"
                    echo "==================="
                    
                    # Cache information
                    CACHE_COUNT=$(find /workspace/argocd-data/cache -name "*.json" -type f 2>/dev/null | wc -l)
                    CACHE_SIZE=$(du -sh /workspace/argocd-data/cache 2>/dev/null | cut -f1 || echo "0B")
                    echo "🗄️  Cache: $CACHE_COUNT files ($CACHE_SIZE)"
                    
                    # Total size
                    TOTAL_SIZE=$(du -sh /workspace/argocd-data 2>/dev/null | cut -f1 || echo "0B")
                    echo "💾 Total workspace size: $TOTAL_SIZE"
                    
                    echo ""
                    echo "🕒 Recent activity:"
                    find /workspace/argocd-data/cache -name "*.json" -type f -mmin -60 2>/dev/null | wc -l | xargs -I {} echo "  {} files cached in the last hour"
                    ;;
                
                "list-cache")
                    echo "🗄️  Cache Files:"
                    echo "==============="
                    find /workspace/argocd-data/cache -name "*.json" -type f -exec basename {} \; 2>/dev/null | sort || echo "No cache files found"
                    echo ""
                    echo "Recent cache files (last 4 hours):"
                    find /workspace/argocd-data/cache -name "*.json" -type f -mmin -240 -exec ls -lh {} \; 2>/dev/null | awk '{print $9, $5, $6, $7, $8}' || echo "No recent cache files"
                    ;;
                
                "cleanup")
                    echo "🧹 Workspace Cleanup:"
                    echo "===================="
                    
                    # Clean old cache files (older than 24 hours)
                    CACHE_CLEANED=$(find /workspace/argocd-data/cache -name "*.json" -type f -mmin +1440 -delete -print 2>/dev/null | wc -l)
                    echo "🗄️  Cleaned $CACHE_CLEANED old cache files (>24 hours)"
                    
                    # Show remaining cache files
                    REMAINING_CACHE=$(find /workspace/argocd-data/cache -name "*.json" -type f 2>/dev/null | wc -l)
                    echo "📊 Remaining cache files: $REMAINING_CACHE"
                    ;;
                
                "clear-cache")
                    echo "🧹 Cache Clear:"
                    echo "==============="
                    CACHE_CLEARED=$(find /workspace/argocd-data/cache -name "*.json" -type f -delete -print 2>/dev/null | wc -l)
                    echo "🗄️  Cleared $CACHE_CLEARED cache files"
                    ;;
                
                "stats")
                    echo "📈 Cache Statistics:"
                    echo "==================="
                    
                    # Application cache stats
                    APP_CACHE=$(find /workspace/argocd-data/cache -name "apps_*.json" -type f 2>/dev/null | wc -l)
                    echo "📱 Application cache files: $APP_CACHE"
                    
                    # Cluster cache stats
                    CLUSTER_CACHE=$(find /workspace/argocd-data/cache -name "clusters_*.json" -type f 2>/dev/null | wc -l)
                    echo "🌐 Cluster cache files: $CLUSTER_CACHE"
                    
                    # Repository cache stats
                    REPO_CACHE=$(find /workspace/argocd-data/cache -name "repos_*.json" -type f 2>/dev/null | wc -l)
                    echo "📦 Repository cache files: $REPO_CACHE"
                    
                    # Individual app cache stats
                    INDIVIDUAL_APP_CACHE=$(find /workspace/argocd-data/cache -name "app_*.json" -type f 2>/dev/null | wc -l)
                    echo "🔍 Individual app cache files: $INDIVIDUAL_APP_CACHE"
                    ;;
                
                *)
                    echo "❌ Unknown action: $ACTION"
                    echo ""
                    echo "Available actions:"
                    echo "• status/info - Show workspace status"
                    echo "• list-cache - List cached files"
                    echo "• cleanup - Clean old cache files (>24 hours)"
                    echo "• clear-cache - Clear all cache files"
                    echo "• stats - Show cache statistics by type"
                    ;;
            esac
            """,
            args=[
                Arg(name="action", description="Action to perform: status, list-cache, cleanup, clear-cache, stats", required=False)
            ],
            image="alpine:latest"
        )

CLITools()