#!/usr/bin/env python3
"""
Script to import data from JSON file to database
"""

import asyncio
import asyncpg
import os
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any


class DatabaseImporter:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
    
    async def connect(self):
        """Connect to the database"""
        if self.database_url.startswith('postgresql+asyncpg://'):
            self.database_url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        self.conn = await asyncpg.connect(self.database_url)
        print("✅ Connected to target database successfully")
    
    async def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            await self.conn.close()
            print("🔌 Database connection closed")
    
    def _parse_interval_to_timedelta(self, interval_str: str) -> timedelta:
        """Parse PostgreSQL interval string to Python timedelta"""
        import re
        
        # Handle common PostgreSQL interval formats
        # Examples: "1 day", "2 hours", "30 minutes", "1 day 2:30:45"
        
        if not interval_str or interval_str.lower() in ['none', 'null']:
            return None
            
        # Parse days
        days_match = re.search(r'(\d+)\s+day', interval_str, re.IGNORECASE)
        days = int(days_match.group(1)) if days_match else 0
        
        # Parse time part (HH:MM:SS)
        time_match = re.search(r'(\d+):(\d+):(\d+(?:\.\d+)?)', interval_str)
        if time_match:
            hours = int(time_match.group(1))
            minutes = int(time_match.group(2))
            seconds = float(time_match.group(3))
        else:
            # Parse individual time components
            hours_match = re.search(r'(\d+)\s+hour', interval_str, re.IGNORECASE)
            hours = int(hours_match.group(1)) if hours_match else 0
            
            minutes_match = re.search(r'(\d+)\s+minute', interval_str, re.IGNORECASE)
            minutes = int(minutes_match.group(1)) if minutes_match else 0
            
            seconds_match = re.search(r'(\d+(?:\.\d+)?)\s+second', interval_str, re.IGNORECASE)
            seconds = float(seconds_match.group(1)) if seconds_match else 0
        
        return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
    
    async def clear_database(self, confirm: bool = False):
        """Clear all data from database (use with caution!)"""
        if not confirm:
            print("⚠️  This will delete ALL data from the database!")
            response = input("Type 'YES' to confirm: ")
            if response != 'YES':
                print("❌ Operation cancelled")
                return False
        
        print("🗑️  Clearing database...")
        
        # Delete in reverse order of dependencies
        tables = ['mutes', 'filter_positions', 'filter_locations', 'filter_companies', 'filters', 'users']
        
        for table in tables:
            try:
                count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                if count > 0:
                    await self.conn.execute(f"DELETE FROM {table}")
                    print(f"   Deleted {count} records from {table}")
            except Exception as e:
                print(f"   Warning: Could not clear {table}: {e}")
        
        print("✅ Database cleared")
        return True
    
    async def import_users(self, users_data: List[Dict[str, Any]]) -> Dict[int, int]:
        """Import users and return mapping of old_id -> new_id"""
        print(f"\n👥 Importing {len(users_data)} users...")
        
        id_mapping = {}
        
        for user in users_data:
            try:
                # Check if user already exists by tg_id
                existing_user = await self.conn.fetchrow("""
                    SELECT id FROM users WHERE tg_id = $1
                """, user['tg_id'])
                
                if existing_user:
                    # User already exists, use existing ID
                    new_id = existing_user['id']
                    print(f"   ✅ User {user['tg_id']} already exists (old_id: {user['id']} -> existing_id: {new_id})")
                else:
                    # Parse datetime fields
                    access_ends = None
                    if user.get('access_ends'):
                        access_ends = datetime.fromisoformat(user['access_ends'].replace('Z', '+00:00'))
                    
                    created_at = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                    
                    # Insert new user
                    new_id = await self.conn.fetchval("""
                        INSERT INTO users (tg_id, is_admin, access_ends, created_at)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id
                    """, user['tg_id'], user['is_admin'], access_ends, created_at)
                    
                    print(f"   ✅ User {user['tg_id']} imported (old_id: {user['id']} -> new_id: {new_id})")
                
                id_mapping[user['id']] = new_id
                
            except Exception as e:
                print(f"   ❌ Failed to import user {user.get('tg_id', 'unknown')}: {e}")
        
        print(f"✅ Processed {len(id_mapping)} users")
        return id_mapping
    
    async def import_filters(self, filters_data: List[Dict[str, Any]], user_id_mapping: Dict[int, int]):
        """Import filters with user ID mapping"""
        print(f"\n🔍 Importing {len(filters_data)} filters...")
        
        filter_id_mapping = {}
        
        for filter_row in filters_data:
            try:
                # Map user_id
                new_user_id = user_id_mapping.get(filter_row['user_id'])
                if not new_user_id:
                    print(f"   ⚠️  Skipping filter {filter_row['id']} - user not found")
                    continue
                
                # Check if filter already exists (optional - you can remove this if you want to allow duplicates)
                existing_filter = await self.conn.fetchrow("""
                    SELECT id FROM filters 
                    WHERE user_id = $1 AND is_black_list = $2 AND is_and = $3 
                    AND longer = $4 AND shorter = $5
                """, new_user_id, filter_row['is_black_list'], filter_row['is_and'], 
                     self._parse_interval_to_timedelta(str(filter_row.get('longer', ''))) if filter_row.get('longer') else None,
                     self._parse_interval_to_timedelta(str(filter_row.get('shorter', ''))) if filter_row.get('shorter') else None)
                
                if existing_filter:
                    print(f"   ⚠️  Filter {filter_row['id']} already exists, skipping")
                    filter_id_mapping[filter_row['id']] = existing_filter['id']
                    continue
                
                # Parse interval fields
                longer = None
                if filter_row.get('longer'):
                    try:
                        # Parse PostgreSQL interval string to timedelta
                        longer_str = str(filter_row['longer'])
                        longer = self._parse_interval_to_timedelta(longer_str)
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not parse longer interval '{filter_row.get('longer')}': {e}")
                        longer = None
                
                shorter = None
                if filter_row.get('shorter'):
                    try:
                        # Parse PostgreSQL interval string to timedelta
                        shorter_str = str(filter_row['shorter'])
                        shorter = self._parse_interval_to_timedelta(shorter_str)
                    except Exception as e:
                        print(f"   ⚠️  Warning: Could not parse shorter interval '{filter_row.get('shorter')}': {e}")
                        shorter = None
                
                # Insert filter
                new_id = await self.conn.fetchval("""
                    INSERT INTO filters (user_id, is_black_list, is_and, longer, shorter)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                """, new_user_id, filter_row['is_black_list'], filter_row['is_and'], longer, shorter)
                
                filter_id_mapping[filter_row['id']] = new_id
                print(f"   ✅ Filter imported (old_id: {filter_row['id']} -> new_id: {new_id})")
                
            except Exception as e:
                print(f"   ❌ Failed to import filter {filter_row.get('id', 'unknown')}: {e}")
        
        print(f"✅ Imported {len(filter_id_mapping)} filters")
        return filter_id_mapping
    
    async def import_filter_details(self, 
                                  companies_data: List[Dict[str, Any]], 
                                  locations_data: List[Dict[str, Any]], 
                                  positions_data: List[Dict[str, Any]], 
                                  filter_id_mapping: Dict[int, int]):
        """Import filter details (companies, locations, positions)"""
        
        # Import companies
        print(f"\n🏢 Importing {len(companies_data)} filter companies...")
        companies_imported = 0
        for company in companies_data:
            try:
                new_filter_id = filter_id_mapping.get(company['filter_id'])
                if not new_filter_id:
                    continue
                
                await self.conn.execute("""
                    INSERT INTO filter_companies (filter_id, company)
                    VALUES ($1, $2)
                """, new_filter_id, company['company'])
                
                companies_imported += 1
            except Exception as e:
                print(f"   ❌ Failed to import company {company.get('company', 'unknown')}: {e}")
        
        print(f"✅ Imported {companies_imported} companies")
        
        # Import locations
        print(f"\n📍 Importing {len(locations_data)} filter locations...")
        locations_imported = 0
        for location in locations_data:
            try:
                new_filter_id = filter_id_mapping.get(location['filter_id'])
                if not new_filter_id:
                    continue
                
                await self.conn.execute("""
                    INSERT INTO filter_locations (filter_id, location)
                    VALUES ($1, $2)
                """, new_filter_id, location['location'])
                
                locations_imported += 1
            except Exception as e:
                print(f"   ❌ Failed to import location {location.get('location', 'unknown')}: {e}")
        
        print(f"✅ Imported {locations_imported} locations")
        
        # Import positions
        print(f"\n👷 Importing {len(positions_data)} filter positions...")
        positions_imported = 0
        for position in positions_data:
            try:
                new_filter_id = filter_id_mapping.get(position['filter_id'])
                if not new_filter_id:
                    continue
                
                await self.conn.execute("""
                    INSERT INTO filter_positions (filter_id, position)
                    VALUES ($1, $2)
                """, new_filter_id, position['position'])
                
                positions_imported += 1
            except Exception as e:
                print(f"   ❌ Failed to import position {position.get('position', 'unknown')}: {e}")
        
        print(f"✅ Imported {positions_imported} positions")
    
    async def import_mutes(self, mutes_data: List[Dict[str, Any]], user_id_mapping: Dict[int, int]):
        """Import mutes with user ID mapping"""
        print(f"\n🔇 Importing {len(mutes_data)} mutes...")
        
        mutes_imported = 0
        for mute in mutes_data:
            try:
                # Map user_id
                new_user_id = user_id_mapping.get(mute['user_id'])
                if not new_user_id:
                    print(f"   ⚠️  Skipping mute {mute['id']} - user not found")
                    continue
                
                # Parse datetime
                created_at = datetime.fromisoformat(mute['created_at'].replace('Z', '+00:00'))
                
                # Insert mute
                await self.conn.execute("""
                    INSERT INTO mutes (user_id, shift_link, created_at)
                    VALUES ($1, $2, $3)
                """, new_user_id, mute['shift_link'], created_at)
                
                mutes_imported += 1
            except Exception as e:
                print(f"   ❌ Failed to import mute {mute.get('id', 'unknown')}: {e}")
        
        print(f"✅ Imported {mutes_imported} mutes")
    
    async def verify_import(self):
        """Verify the imported data"""
        print("\n🔍 Verifying imported data...")
        
        # Count records in each table
        users_count = await self.conn.fetchval("SELECT COUNT(*) FROM users")
        filters_count = await self.conn.fetchval("SELECT COUNT(*) FROM filters")
        mutes_count = await self.conn.fetchval("SELECT COUNT(*) FROM mutes")
        companies_count = await self.conn.fetchval("SELECT COUNT(*) FROM filter_companies")
        locations_count = await self.conn.fetchval("SELECT COUNT(*) FROM filter_locations")
        positions_count = await self.conn.fetchval("SELECT COUNT(*) FROM filter_positions")
        
        print(f"📊 Imported data:")
        print(f"   👥 Users: {users_count}")
        print(f"   🔍 Filters: {filters_count}")
        print(f"   🔇 Mutes: {mutes_count}")
        print(f"   🏢 Companies: {companies_count}")
        print(f"   📍 Locations: {locations_count}")
        print(f"   👷 Positions: {positions_count}")
        
        # Check for active users
        active_users = await self.conn.fetchval("""
            SELECT COUNT(*) FROM users 
            WHERE access_ends IS NOT NULL AND access_ends > NOW()
        """)
        admin_users = await self.conn.fetchval("SELECT COUNT(*) FROM users WHERE is_admin = true")
        
        print(f"   ✅ Active users: {active_users}")
        print(f"   👑 Admin users: {admin_users}")
    
    async def import_from_file(self, file_path: str, clear_db: bool = False):
        """Import data from JSON file"""
        print(f"📁 Reading data from {file_path}...")
        
        if not Path(file_path).exists():
            print(f"❌ File not found: {file_path}")
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            return False
        
        print(f"✅ File loaded successfully")
        print(f"📅 Export timestamp: {data.get('export_timestamp', 'Unknown')}")
        
        # Clear database if requested
        if clear_db:
            if not await self.clear_database():
                return False
        
        try:
            # Import users first (they are referenced by other tables)
            user_id_mapping = await self.import_users(data.get('users', []))
            
            # Import filters
            filter_id_mapping = await self.import_filters(data.get('filters', []), user_id_mapping)
            
            # Import filter details
            await self.import_filter_details(
                data.get('filter_companies', []),
                data.get('filter_locations', []),
                data.get('filter_positions', []),
                filter_id_mapping
            )
            
            # Import mutes
            await self.import_mutes(data.get('mutes', []), user_id_mapping)
            
            # Verify import
            await self.verify_import()
            
            print("\n🎉 Data import completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Import failed: {e}")
            return False


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Import database data from JSON file')
    parser.add_argument('file', help='JSON file to import from')
    parser.add_argument('--database-url', help='Database URL (overrides DATABASE_URL env var)')
    parser.add_argument('--clear', action='store_true', help='Clear database before import')
    parser.add_argument('--confirm-clear', action='store_true', help='Skip confirmation for clearing database')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL', 'postgresql://tjv:tjv@postgres:5432/tjv')
    
    print("🚀 Starting database data import...")
    print(f"📁 Source file: {args.file}")
    print(f"🔗 Target database: {database_url}")
    
    if args.clear:
        print("⚠️  Database will be cleared before import!")
    
    importer = DatabaseImporter(database_url)
    
    try:
        await importer.connect()
        
        success = await importer.import_from_file(args.file, args.clear)
        
        if success:
            print("\n✨ Import completed successfully!")
        else:
            print("\n❌ Import failed!")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    finally:
        await importer.disconnect()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
