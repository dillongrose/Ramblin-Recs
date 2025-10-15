#!/usr/bin/env python3
"""
Simple script to run the Georgia Tech events ingestion
"""

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.simple_gatech_scraper import main

if __name__ == "__main__":
    print("🚀 Starting Georgia Tech events ingestion...")
    asyncio.run(main())

