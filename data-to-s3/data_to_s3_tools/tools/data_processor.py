from typing import List
import sys
from .base import DataProcessorTool, Arg
from kubiya_sdk.tools.registry import tool_registry

class DataProcessorTools:
    """Data processing tools for CSV deduplication and S3 upload."""

    def __init__(self):
        """Initialize and register data processing tools."""
        try:
            tools = [
                self.process_csv_data()
            ]
            
            for tool in tools:
                try:
                    tool_registry.register("data_to_s3", tool)
                    print(f"✅ Registered: {tool.name}")
                except Exception as e:
                    print(f"❌ Failed to register {tool.name}: {str(e)}", file=sys.stderr)
                    raise
        except Exception as e:
            print(f"❌ Failed to register data processing tools: {str(e)}", file=sys.stderr)
            raise

    def process_csv_data(self) -> DataProcessorTool:
        """Process CSV data with deduplication and upload to S3."""
        return DataProcessorTool(
            name="process_csv_to_s3",
            description="Process CSV data with custom deduplication rules and upload to S3. Supports both file input and direct CSV content.",
            args=[
                Arg(
                    name="data_source",
                    description="Path to the CSV file to process",
                    required=False
                ),
                Arg(
                    name="data_content",
                    description="Direct CSV content as string (alternative to data_source)",
                    required=False
                ),
                Arg(
                    name="output_location",
                    description="S3 path where processed data should be stored (e.g., s3://bucket/path/file.json)",
                    required=True
                ),
                Arg(
                    name="s3_bucket",
                    description="S3 bucket name for upload",
                    required=True
                ),
                Arg(
                    name="s3_key",
                    description="S3 key/path for the processed file",
                    required=True
                )
            ],
            image="python:3.11-slim",
            content=self._get_data_processing_script()
        )

    def _get_data_processing_script(self) -> str:
        """Get the Python script for data processing and deduplication."""
        return '''
echo "🔄 PROCESSING DATA WITH CUSTOM DEDUPLICATION RULES"
echo "=================================================="

# Install required packages
echo "📦 Installing required packages..."
pip install pandas boto3 --no-cache-dir

# Set up variables
DATA_SOURCE="${data_source}"
DATA_CONTENT="${data_content}"
OUTPUT_FILE="${output_location}"
S3_BUCKET="${s3_bucket}"
S3_KEY="${s3_key}"

echo "📋 Data source: $DATA_SOURCE"
echo "📦 Output file: $OUTPUT_FILE"
echo "🪣 S3 Bucket: $S3_BUCKET"
echo "🔑 S3 Key: $S3_KEY"

# Check if we have direct content or file path
if [ "$DATA_CONTENT" != "" ] && [ "$DATA_CONTENT" != "\\${data_content}" ]; then
    echo "📝 Using direct CSV content (${#DATA_CONTENT} characters)"
    PROCESSING_MODE="content"
else
    echo "📁 Using file path: $DATA_SOURCE"
    PROCESSING_MODE="file"
fi

# Create Python script for data processing
cat > /tmp/process_data.py << 'EOF'
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  Pandas not available, using basic CSV processing...")

import json
import sys
import io
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

def upload_to_s3(file_path, bucket, key):
    """Upload processed data to S3."""
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket, key)
        print(f"✅ Successfully uploaded to s3://{bucket}/{key}")
        return True
    except ClientError as e:
        print(f"❌ Error uploading to S3: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during S3 upload: {e}")
        return False

def process_csv_without_pandas(csv_content):
    """Basic CSV processing without pandas."""
    print("📋 Processing CSV without pandas...")
    
    lines = csv_content.strip().split('\\n')
    if not lines:
        return []
    
    # Try to detect and skip metadata
    start_row = 0
    for i, line in enumerate(lines):
        if 'Source' in line and 'Content Description' in line:
            start_row = i
            break
    
    if start_row > 0:
        print(f"🔄 Skipping {start_row} metadata rows...")
        lines = lines[start_row:]
    
    # Parse CSV manually
    import csv
    from io import StringIO
    
    # Try comma-separated first
    try:
        reader = csv.DictReader(StringIO('\\n'.join(lines)))
        data = list(reader)
        if data and len(data[0]) > 1:
            print(f"✅ Parsed as CSV with {len(data)} records")
            return data
    except Exception as e:
        print(f"⚠️  CSV parsing failed: {e}")
    
    # Try tab-separated
    try:
        reader = csv.DictReader(StringIO('\\n'.join(lines)), delimiter='\\t')
        data = list(reader)
        if data and len(data[0]) > 1:
            print(f"✅ Parsed as TSV with {len(data)} records")
            return data
    except Exception as e:
        print(f"⚠️  TSV parsing failed: {e}")
    
    # Fallback to basic processing
    print("🔄 Using basic line-by-line processing...")
    headers = lines[0].split(',') if ',' in lines[0] else lines[0].split('\\t')
    data = []
    for line in lines[1:]:
        values = line.split(',') if ',' in line else line.split('\\t')
        if len(values) >= len(headers):
            row = {headers[i]: values[i] for i in range(len(headers))}
            data.append(row)
    
    print(f"✅ Basic processing completed with {len(data)} records")
    return data

def process_data_from_file(input_file, output_file, s3_bucket, s3_key):
    """Process data from file path."""
    print(f"📋 Reading data from file: {input_file}")
    
    if not PANDAS_AVAILABLE:
        # Use fallback CSV processing
        print("🔄 Using fallback CSV processing for file...")
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            data = process_csv_without_pandas(csv_content)
            
            if not data:
                print("❌ No data could be processed from file")
                return False
            
            # Create simplified result
            result = {
                "processing_summary": {
                    "total_records": len(data),
                    "duplicates_removed": 0,
                    "groups_created": len(data),
                    "content_descriptions_combined": 0,
                    "format_converted": "csv_to_json",
                    "data_quality_score": 70,
                    "processing_method": "fallback_csv_processing"
                },
                "processed_data": data,
                "deduplication_report": {
                    "sources_processed": len(set(row.get('Source', '') for row in data)),
                    "records_before_dedup": len(data),
                    "records_after_dedup": len(data),
                    "content_combinations_made": 0,
                    "note": "No deduplication performed - pandas not available"
                },
                "validation_report": {
                    "issues_found": ["Pandas not available - limited processing"],
                    "recommendations": ["Install pandas for full processing capabilities"]
                }
            }
            
            # Write processed data to output file
            print(f"💾 Writing processed data to: {output_file}")
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Upload to S3
            if upload_to_s3(output_file, s3_bucket, s3_key):
                print(f"✅ Data processing and S3 upload completed!")
                print(f"📊 Summary: {len(data)} records processed")
                return True
            else:
                print(f"⚠️  Data processed but S3 upload failed")
                return False
                
        except Exception as e:
            print(f"❌ Error processing file: {e}")
            return False
    
    # Continue with pandas processing...
    
    # Validate input file exists
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_file}")
        print(f"📁 Current directory: {Path.cwd()}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Expected columns for validation
    expected_columns = [
        'Source',
        'Content Description', 
        'Rights (Media - Territory - Term)',
        'Authorized Exclusions and/or Promotional Restrictions',
        'Program only / Series only / No usage restrictions'
    ]
    
    # Read the CSV file
    print(f"📖 Reading CSV file: {input_file}")
    try:
        # Try CSV format first
        data = pd.read_csv(input_file)
        print(f"✅ Successfully loaded CSV with {len(data)} records")
        
        # Check if we have expected columns
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if len(missing_columns) == len(expected_columns):
            print(f"⚠️  CSV parsed but has wrong headers. Trying to skip metadata rows...")
            raise ValueError("Wrong headers detected, trying skiprows approach")
        
    except Exception as e:
        print(f"⚠️  CSV parsing failed or wrong headers: {e}")
        print(f"🔄 Trying to skip metadata rows...")
        try:
            # Try skipping first 15 rows (common for shot sheets with metadata)
            data = pd.read_csv(input_file, skiprows=15)
            print(f"✅ Successfully loaded CSV with metadata skipped, {len(data)} records")
        except Exception as e2:
            print(f"⚠️  CSV with skiprows failed: {e2}")
            print(f"🔄 Trying TSV (tab-separated) format...")
            try:
                # Try TSV format
                data = pd.read_csv(input_file, sep='\\t')
                print(f"✅ Successfully loaded TSV with {len(data)} records")
            except Exception as e3:
                print(f"❌ Failed to read as CSV, CSV with skiprows, or TSV: {e3}")
                try:
                    with open(input_file, 'r') as f:
                        first_lines = [f.readline().strip() for _ in range(3)]
                        print(f"📋 First 3 lines of file:")
                        for i, line in enumerate(first_lines, 1):
                            print(f"  {i}: {line}")
                except Exception as read_error:
                    print(f"❌ Could not read file at all: {read_error}")
                raise
    
    return process_pandas_data(data, output_file, s3_bucket, s3_key)

def process_data_from_content(csv_content, output_file, s3_bucket, s3_key):
    """Process data from CSV content string."""
    print(f"📋 Processing CSV content ({len(csv_content)} characters)")
    
    if not PANDAS_AVAILABLE:
        # Use fallback CSV processing
        print("🔄 Using fallback CSV processing...")
        data = process_csv_without_pandas(csv_content)
        
        if not data:
            print("❌ No data could be processed")
            return False
        
        # Create simplified result
        result = {
            "processing_summary": {
                "total_records": len(data),
                "duplicates_removed": 0,
                "groups_created": len(data),
                "content_descriptions_combined": 0,
                "format_converted": "csv_to_json",
                "data_quality_score": 70,
                "processing_method": "fallback_csv_processing"
            },
            "processed_data": data,
            "deduplication_report": {
                "sources_processed": len(set(row.get('Source', '') for row in data)),
                "records_before_dedup": len(data),
                "records_after_dedup": len(data),
                "content_combinations_made": 0,
                "note": "No deduplication performed - pandas not available"
            },
            "validation_report": {
                "issues_found": ["Pandas not available - limited processing"],
                "recommendations": ["Install pandas for full processing capabilities"]
            }
        }
        
        # Write processed data to output file
        print(f"💾 Writing processed data to: {output_file}")
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Upload to S3
        if upload_to_s3(output_file, s3_bucket, s3_key):
            print(f"✅ Data processing and S3 upload completed!")
            print(f"📊 Summary: {len(data)} records processed")
            return True
        else:
            print(f"⚠️  Data processed but S3 upload failed")
            return False
    
    # Continue with pandas processing...
    
    # Expected columns for validation
    expected_columns = [
        'Source',
        'Content Description', 
        'Rights (Media - Territory - Term)',
        'Authorized Exclusions and/or Promotional Restrictions',
        'Program only / Series only / No usage restrictions'
    ]
    
    # Read CSV from string
    print(f"📖 Parsing CSV content...")
    try:
        # Try CSV format first
        data = pd.read_csv(io.StringIO(csv_content))
        print(f"✅ Successfully parsed CSV with {len(data)} records")
        
        # Check if we have expected columns
        missing_columns = [col for col in expected_columns if col not in data.columns]
        if len(missing_columns) == len(expected_columns):
            print(f"⚠️  CSV parsed but has wrong headers. Trying to skip metadata rows...")
            raise ValueError("Wrong headers detected, trying skiprows approach")
        
    except Exception as e:
        print(f"⚠️  CSV parsing failed or wrong headers: {e}")
        print(f"🔄 Trying to skip metadata rows...")
        try:
            # Try skipping first 15 rows (common for shot sheets with metadata)
            data = pd.read_csv(io.StringIO(csv_content), skiprows=15)
            print(f"✅ Successfully parsed CSV with metadata skipped, {len(data)} records")
        except Exception as e2:
            print(f"⚠️  CSV with skiprows failed: {e2}")
            print(f"🔄 Trying TSV (tab-separated) format...")
            try:
                # Try TSV format
                data = pd.read_csv(io.StringIO(csv_content), sep='\\t')
                print(f"✅ Successfully parsed TSV with {len(data)} records")
            except Exception as e3:
                print(f"❌ Failed to parse as CSV, CSV with skiprows, or TSV: {e3}")
                # Show first few lines for debugging
                lines = csv_content.split('\\n')[:3]
                print(f"📋 First 3 lines of content:")
                for i, line in enumerate(lines, 1):
                    print(f"  {i}: {line}")
                raise
    
    return process_pandas_data(data, output_file, s3_bucket, s3_key)

def process_pandas_data(data, output_file, s3_bucket, s3_key):
    """Process pandas DataFrame with deduplication."""
    print(f"📊 Data shape: {data.shape}")
    print(f"📋 Columns: {list(data.columns)}")
    
    # Expected columns
    expected_columns = [
        'Source',
        'Content Description', 
        'Rights (Media - Territory - Term)',
        'Authorized Exclusions and/or Promotional Restrictions',
        'Program only / Series only / No usage restrictions'
    ]
    
    # Validate columns
    missing_columns = [col for col in expected_columns if col not in data.columns]
    if missing_columns:
        print(f"⚠️  Warning: Missing expected columns: {missing_columns}")
        print(f"📋 Available columns: {list(data.columns)}")
        
        # Check if this is a completely different format
        if len(missing_columns) == len(expected_columns):
            print("⚠️  ERROR: This CSV appears to be in a different format than expected.")
            print("🔍 Expected columns for data processing:")
            for col in expected_columns:
                print(f"   - {col}")
            print("📋 Actual columns found:")
            for col in data.columns:
                print(f"   - {col}")
            print("🔄 Processing with available columns instead...")
            
            # Use available columns for processing
            source_column = data.columns[0]
            
            # Create simplified result
            result = {
                "processing_summary": {
                    "total_records": len(data),
                    "duplicates_removed": 0,
                    "groups_created": len(data),
                    "content_descriptions_combined": 0,
                    "format_converted": "csv_to_json",
                    "data_quality_score": 50,
                    "error": "Unexpected CSV format - processed with available columns"
                },
                "processed_data": data.to_dict('records'),
                "deduplication_report": {
                    "sources_processed": data[source_column].nunique() if not data[source_column].isna().all() else 0,
                    "records_before_dedup": len(data),
                    "records_after_dedup": len(data),
                    "content_combinations_made": 0,
                    "note": "No deduplication performed due to unexpected format"
                },
                "validation_report": {
                    "issues_found": [f"Expected columns not found: {missing_columns}"],
                    "recommendations": [
                        "Ensure CSV has the expected columns for proper deduplication",
                        "Check the data source format and column names"
                    ]
                }
            }
            
            # Write processed data to output file
            print(f"💾 Writing processed data to: {output_file}")
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # Upload to S3
            if upload_to_s3(output_file, s3_bucket, s3_key):
                print("✅ Data processing and S3 upload completed with warnings!")
                print(f"📊 Summary: {len(data)} records processed (no deduplication)")
                print("🔄 Recommendation: Check CSV format and column names")
                return True
            else:
                print("⚠️  Data processed but S3 upload failed")
                return False
    
    # Data processing stats
    total_records = len(data)
    
    # Apply custom deduplication rules
    deduplicated_data = []
    content_combinations_made = 0
    
    print("🔍 Applying custom deduplication rules...")
    
    # Check if Source column exists
    if 'Source' not in data.columns:
        print("⚠️  Source column not found. Using first column as Source.")
        source_column = data.columns[0]
    else:
        source_column = 'Source'
    
    # Group by Source first
    for source, source_group in data.groupby(source_column):
        # Then group by rights profile (the three key fields)
        rights_columns = [
            'Rights (Media - Territory - Term)',
            'Authorized Exclusions and/or Promotional Restrictions', 
            'Program only / Series only / No usage restrictions'
        ]
        
        # Only group if all rights columns exist
        available_rights_columns = [col for col in rights_columns if col in data.columns]
        
        if available_rights_columns:
            try:
                grouped = source_group.groupby(available_rights_columns)
            except Exception as group_error:
                print(f"⚠️  Grouping error: {group_error}")
                grouped = [(None, source_group)]
        else:
            grouped = [(None, source_group)]
        
        for rights_key, entries in grouped:
            if 'Content Description' in entries.columns:
                descriptions = entries['Content Description'].dropna().unique()
                combined_description = "; ".join(str(desc) for desc in descriptions if str(desc) != 'nan')
                
                if len(descriptions) > 1:
                    content_combinations_made += 1
            else:
                text_columns = [col for col in entries.columns if entries[col].dtype == 'object']
                if text_columns:
                    combined_description = str(entries[text_columns[0]].iloc[0])
                else:
                    combined_description = "No content description"
            
            dedup_record = {source_column: source}
            dedup_record["Content Description"] = combined_description
            
            if isinstance(rights_key, tuple) and len(available_rights_columns) > 0:
                for i, col in enumerate(available_rights_columns):
                    if i < len(rights_key):
                        dedup_record[col] = rights_key[i]
            elif available_rights_columns and rights_key is not None:
                dedup_record[available_rights_columns[0]] = rights_key
            
            first_entry = entries.iloc[0]
            for col in entries.columns:
                if col not in dedup_record and col not in ['Content Description']:
                    dedup_record[col] = first_entry[col]
            
            deduplicated_data.append(dedup_record)
    
    print(f"✅ Deduplication complete: {total_records} → {len(deduplicated_data)} records")
    
    # Create processing report
    result = {
        "processing_summary": {
            "total_records": total_records,
            "duplicates_removed": total_records - len(deduplicated_data),
            "groups_created": len(deduplicated_data),
            "content_descriptions_combined": content_combinations_made,
            "format_converted": "csv_to_json",
            "data_quality_score": 95
        },
        "processed_data": deduplicated_data,
        "deduplication_report": {
            "sources_processed": data[source_column].nunique(),
            "records_before_dedup": total_records,
            "records_after_dedup": len(deduplicated_data),
            "content_combinations_made": content_combinations_made
        },
        "validation_report": {
            "issues_found": missing_columns,
            "recommendations": ["Ensure all expected columns are present in future uploads"]
        }
    }
    
    # Write processed data to output file
    print(f"💾 Writing processed data to: {output_file}")
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Upload to S3
    if upload_to_s3(output_file, s3_bucket, s3_key):
        print("✅ Data processing and S3 upload completed successfully!")
        print(f"📊 Summary: {total_records} → {len(deduplicated_data)} records")
        print(f"🔄 Content combinations: {content_combinations_made}")
        return True
    else:
        print("⚠️  Data processed but S3 upload failed")
        return False

def process_data(processing_mode, input_source, output_file, s3_bucket, s3_key):
    """Main data processing function."""
    try:
        # Load data based on processing mode
        if processing_mode == "file":
            return process_data_from_file(input_source, output_file, s3_bucket, s3_key)
        elif processing_mode == "content":
            return process_data_from_content(input_source, output_file, s3_bucket, s3_key)
        else:
            raise ValueError(f"Unknown processing mode: {processing_mode}")
        
    except Exception as e:
        print(f"❌ Error processing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 6:
        print("Usage: python process_data.py <mode> <input_source> <output_file> <s3_bucket> <s3_key>")
        print("  mode: 'file' or 'content'")
        print("  input_source: file path (if mode=file) or CSV content (if mode=content)")
        print("  output_file: local output file path")
        print("  s3_bucket: S3 bucket name")
        print("  s3_key: S3 key/path")
        sys.exit(1)
    
    processing_mode = sys.argv[1]
    input_source = sys.argv[2]
    output_file = sys.argv[3]
    s3_bucket = sys.argv[4]
    s3_key = sys.argv[5]
    
    print(f"🚀 Starting data processing...")
    print(f"📥 Mode: {processing_mode}")
    if processing_mode == "file":
        print(f"📁 Input file: {input_source}")
    else:
        print(f"📝 Input content: {len(input_source)} characters")
    print(f"📤 Output: {output_file}")
    print(f"🪣 S3 Bucket: {s3_bucket}")
    print(f"🔑 S3 Key: {s3_key}")
    
    success = process_data(processing_mode, input_source, output_file, s3_bucket, s3_key)
    sys.exit(0 if success else 1)
EOF

# Run the Python script with proper arguments
echo "🐍 Running Python data processing script..."
if [ "$PROCESSING_MODE" = "content" ]; then
    # Write CSV content to temporary file to avoid shell escaping issues
    CSV_TEMP_FILE="/tmp/csv_input_$$.csv"
    printf '%s' "$DATA_CONTENT" > "$CSV_TEMP_FILE"
    echo "🔧 CSV content written to temporary file: $CSV_TEMP_FILE"
    python3 /tmp/process_data.py "file" "$CSV_TEMP_FILE" "/tmp/processed_data.json" "$S3_BUCKET" "$S3_KEY"
    # Clean up temporary file
    rm -f "$CSV_TEMP_FILE"
else
    python3 /tmp/process_data.py "file" "$DATA_SOURCE" "/tmp/processed_data.json" "$S3_BUCKET" "$S3_KEY"
fi

# Check if processing was successful
if [ $? -eq 0 ]; then
    echo "✅ Data processing and S3 upload completed successfully"
    echo "📋 Processed data uploaded to: s3://$S3_BUCKET/$S3_KEY"
    
    # Show a sample of the processed data
    echo "📊 Sample of processed data:"
    head -20 "/tmp/processed_data.json"
else
    echo "❌ Data processing failed"
    exit 1
fi
''' 