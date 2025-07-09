#!/bin/bash

# Debug script to test the exact query format
echo "Debug: Testing query format..."

# Test with the exact format the AI is sending
opal_query='filter severity == \"error\"'
echo "Query variable: $opal_query"

# Test the validation
if echo "$opal_query" | grep -q '"[^"]*"[^"]*"'; then
    echo "❌ FAILED: Query contains unescaped quotes"
else
    echo "✅ PASSED: Query format is valid"
fi

# Test the echo statement that's failing
echo "Query: $opal_query"

# Test the grep pattern that's causing issues
if echo "$opal_query" | grep -q "filter.*severity.*error"; then
    echo "Note: Query format looks good for error filtering"
fi

echo "Debug completed!" 