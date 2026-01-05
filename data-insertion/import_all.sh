#!/bin/bash
# Script to cleanup and import recipe data
# Usage: ./import_all.sh [author_user_id]

AUTHOR_ID=${1:-1}

echo "=========================================="
echo "Recipe Data Import Script"
echo "=========================================="
echo ""
echo "Step 1: Cleaning up existing data..."
echo "Running cleanup_tables.sql..."
python manage.py dbshell < cleanup_tables.sql

if [ $? -ne 0 ]; then
    echo "❌ Cleanup failed! Aborting."
    exit 1
fi

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "Step 2: Importing new recipe data..."
echo "Running Ashpazyar-data.sql..."
python manage.py dbshell < Ashpazyar-data.sql

if [ $? -ne 0 ]; then
    echo "❌ Import failed!"
    exit 1
fi

echo ""
echo "✅ Import completed successfully!"
echo ""
echo "Summary:"
echo "  - All recipe-related tables have been cleared"
echo "  - New data has been imported"
echo "  - Author ID used: $AUTHOR_ID"
echo ""
echo "Note: Users table was NOT modified"

