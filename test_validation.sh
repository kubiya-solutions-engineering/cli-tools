#!/bin/bash

# Test the validation logic
echo "Testing validation logic..."

# Test 1: Valid query with proper escaping
echo "Test 1: Valid query with proper escaping"
opal_query='\"filter severity == \\\"error\\\"\"'
echo "Query: $opal_query"

if echo "$opal_query" | grep -q '"[^\\]*"[^\\]*"'; then
    echo "❌ FAILED: Query contains unescaped quotes"
else
    echo "✅ PASSED: Query format is valid"
fi

echo ""

# Test 2: Invalid query with unescaped quotes (what the AI is sending)
echo "Test 2: Invalid query with unescaped quotes"
opal_query='filter severity == "error"'
echo "Query: $opal_query"

# Check if the query contains any unescaped double quotes
if echo "$opal_query" | grep -q '"' && ! echo "$opal_query" | grep -q '\\"'; then
    echo "❌ FAILED: Query contains unescaped quotes (expected)"
else
    echo "✅ PASSED: Query format is valid (unexpected)"
fi

echo ""

# Test 3: Another invalid query
echo "Test 3: Another invalid query"
opal_query='"filter severity == "error""'
echo "Query: $opal_query"

# Check if the query contains any unescaped double quotes
if echo "$opal_query" | grep -q '"' && ! echo "$opal_query" | grep -q '\\"'; then
    echo "❌ FAILED: Query contains unescaped quotes (expected)"
else
    echo "✅ PASSED: Query format is valid (unexpected)"
fi

echo "Test completed!" 