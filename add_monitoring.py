#!/usr/bin/env python3
"""
Add detailed monitoring and logging to track processing times
"""

import json
import os
from datetime import datetime

def add_timing_logs():
    """Add timing logs to main.py"""
    
    # Read main.py
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Check if monitoring already added
    if 'MONITORING_START' in content:
        print("✅ Monitoring already added")
        return
    
    # Add monitoring imports and setup
    monitoring_setup = '''
# Monitoring and Performance Tracking
import time
from typing import Dict, Any

# Global timing tracker
_timing_data = {}

def log_timing(operation: str, duration_ms: float, details: Dict[str, Any] = None):
    """Log timing information for monitoring"""
    if operation not in _timing_data:
        _timing_data[operation] = []
    _timing_data[operation].append({
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    })
    print(f"⏱️  {operation}: {duration_ms:.2f}ms")

def get_timing_summary() -> Dict[str, Any]:
    """Get summary of all timing data"""
    summary = {}
    for operation, timings in _timing_data.items():
        durations = [t["duration_ms"] for t in timings]
        summary[operation] = {
            "count": len(timings),
            "avg_ms": sum(durations) / len(durations) if durations else 0,
            "min_ms": min(durations) if durations else 0,
            "max_ms": max(durations) if durations else 0,
            "last_ms": durations[-1] if durations else 0
        }
    return summary
'''
    
    # Find where to insert (after imports)
    import_end = content.find('load_dotenv()')
    if import_end == -1:
        import_end = content.find('from dotenv import load_dotenv')
    
    if import_end != -1:
        # Find end of that line
        line_end = content.find('\n', import_end)
        # Insert monitoring setup
        new_content = content[:line_end+1] + monitoring_setup + content[line_end+1:]
        
        with open('main.py', 'w') as f:
            f.write(new_content)
        
        print("✅ Added monitoring setup to main.py")
    else:
        print("⚠️  Could not find insertion point")

if __name__ == "__main__":
    add_timing_logs()
