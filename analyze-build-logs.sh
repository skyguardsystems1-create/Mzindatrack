#!/bin/bash
# Build Log Analyzer - Extracts and summarizes errors from buildozer logs
# Outputs ONLY essential errors and warnings in KB format
# Usage: ./analyze-build-logs.sh <path-to-build.log>

set -e

LOG_FILE="${1:-.buildozer/logs/run_*.log}"
OUTPUT_FILE="build-errors-summary.txt"

if [ ! -f "$LOG_FILE" ] && [ "$1" = "" ]; then
  LOG_FILE=$(find .buildozer/logs -name "run_*.log" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
  if [ -z "$LOG_FILE" ]; then
    echo "❌ No buildozer logs found"
    exit 1
  fi
fi

# Start output
{
  echo "🔍 BUILD LOG SUMMARY"
  echo "===================="
  echo ""
  
  # File info
  ORIGINAL_SIZE=$(du -h "$LOG_FILE" | cut -f1)
  ORIGINAL_KB=$(du -k "$LOG_FILE" | cut -f1)
  echo "📄 Original log: $ORIGINAL_SIZE ($ORIGINAL_KB KB)"
  echo ""
  
  # Extract ONLY errors
  echo "🚨 CRITICAL ERRORS:"
  echo "───────────────────"
  grep -i "error\|failed\|exception\|fatal" "$LOG_FILE" 2>/dev/null | grep -v "^\s*$" | sort -u | head -20 || echo "None"
  echo ""
  
  # Extract build failure info
  echo "❌ BUILD FAILURES:"
  echo "──────────────────"
  grep -i "build failed\|build error\|compilation failed" "$LOG_FILE" 2>/dev/null | head -10 || echo "None"
  echo ""
  
  # Extract linking issues
  echo "🔗 LINKING ISSUES:"
  echo "──────────────────"
  grep -i "undefined reference\|ld.so\|linker error\|cannot find" "$LOG_FILE" 2>/dev/null | head -10 || echo "None"
  echo ""
  
  # Extract Java/Gradle issues
  echo "☕ JAVA/GRADLE ISSUES:"
  echo "─────────────────────"
  grep -i "gradle\|java\|javac\|classpath\|FAILED\s*BUILD" "$LOG_FILE" 2>/dev/null | head -10 || echo "None"
  echo ""
  
  # Extract Python/Cython issues
  echo "🐍 PYTHON/CYTHON ISSUES:"
  echo "────────────────────────"
  grep -i "cython\|python.*error\|setuptools\|distutils" "$LOG_FILE" 2>/dev/null | head -10 || echo "None"
  echo ""
  
  # Extract NDK/SDK issues
  echo "🎯 NDK/SDK ISSUES:"
  echo "──────────────────"
  grep -i "ndk\|sdk\|android.*error\|clang\|toolchain.*not found" "$LOG_FILE" 2>/dev/null | head -10 || echo "None"
  echo ""
  
  # Key warnings
  echo "⚠️ KEY WARNINGS:"
  echo "────────────────"
  grep -i "warning\|deprecated" "$LOG_FILE" 2>/dev/null | sort -u | head -10 || echo "None"
  echo ""
  
  # Statistics
  echo "📊 STATISTICS:"
  echo "───────────────"
  ERROR_COUNT=$(grep -ic "error\|failed" "$LOG_FILE" 2>/dev/null || echo "0")
  WARNING_COUNT=$(grep -ic "warning" "$LOG_FILE" 2>/dev/null || echo "0")
  TOTAL_LINES=$(wc -l < "$LOG_FILE")
  
  echo "Errors: $ERROR_COUNT"
  echo "Warnings: $WARNING_COUNT"
  echo "Total lines: $TOTAL_LINES"
  echo ""
  
  # Last meaningful lines
  echo "🎯 LAST ERROR (usually the root cause):"
  echo "───────────────────────────────────────"
  grep -i "error\|failed\|exception" "$LOG_FILE" 2>/dev/null | tail -3 || echo "None"
  echo ""
  
  # Final 20 lines
  echo "📌 FINAL OUTPUT (last 20 lines):"
  echo "────────────────────────────────"
  tail -20 "$LOG_FILE"
  
} > "$OUTPUT_FILE"

# Show file size
OUTPUT_SIZE=$(du -k "$OUTPUT_FILE" | cut -f1)
echo ""
echo "✅ Summary saved to: $OUTPUT_FILE ($OUTPUT_SIZE KB)"
echo "   Compressed by: $((ORIGINAL_KB / OUTPUT_SIZE))x"
echo ""
cat "$OUTPUT_FILE"
