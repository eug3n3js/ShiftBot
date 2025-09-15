#!/usr/bin/env python3
"""
Script to read data from database and export to JSON file
"""

import asyncio
import asyncpg
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class DatabaseReader:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
    
    async def connect(self):
        """Connect to the database"""
        if self.database_url.startswith('postgresql+asyncpg://'):
            self.database_url = self.database_url.replace('postgresql+asyncpg://', 'postgresql://')
        
        self.conn = await asyncpg.connect(self.database_url)
        print("✅ Connected to database successfully")
    
    async def disconnect(self):
        """Disconnect from the database"""
        if self.conn:
            await self.conn.close()
            print("🔌 Database connection closed")
    
    async def read_users(self) -> List[Dict[str, Any]]:
        """Read all users from database"""
        print("👥 Reading users...")
        
        users = await self.conn.fetch("""
            SELECT id, tg_id, is_admin, access_ends, created_at
            FROM users
            ORDER BY id
        """)
        
        users_data = []
        for user in users:
            user_dict = {
                'id': user['id'],
                'tg_id': user['tg_id'],
                'is_admin': user['is_admin'],
                'access_ends': user['access_ends'].isoformat() if user['access_ends'] else None,
                'created_at': user['created_at'].isoformat()
            }
            users_data.append(user_dict)
        
        print(f"✅ Read {len(users_data)} users")
        return users_data
    
    async def read_filters(self) -> List[Dict[str, Any]]:
        """Read all filters from database"""
        print("🔍 Reading filters...")
        
        filters = await self.conn.fetch("""
            SELECT id, user_id, is_black_list, is_and, longer, shorter
            FROM filters
            ORDER BY id
        """)
        
        filters_data = []
        for filter_row in filters:
            filter_dict = {
                'id': filter_row['id'],
                'user_id': filter_row['user_id'],
                'is_black_list': filter_row['is_black_list'],
                'is_and': filter_row['is_and'],
                'longer': str(filter_row['longer']) if filter_row['longer'] else None,
                'shorter': str(filter_row['shorter']) if filter_row['shorter'] else None
            }
            filters_data.append(filter_dict)
        
        print(f"✅ Read {len(filters_data)} filters")
        return filters_data
    
    async def read_filter_companies(self) -> List[Dict[str, Any]]:
        """Read all filter companies from database"""
        print("🏢 Reading filter companies...")
        
        companies = await self.conn.fetch("""
            SELECT filter_id, company
            FROM filter_companies
            ORDER BY filter_id, company
        """)
        
        companies_data = []
        for company in companies:
            company_dict = {
                'filter_id': company['filter_id'],
                'company': company['company']
            }
            companies_data.append(company_dict)
        
        print(f"✅ Read {len(companies_data)} filter companies")
        return companies_data
    
    async def read_filter_locations(self) -> List[Dict[str, Any]]:
        """Read all filter locations from database"""
        print("📍 Reading filter locations...")
        
        locations = await self.conn.fetch("""
            SELECT filter_id, location
            FROM filter_locations
            ORDER BY filter_id, location
        """)
        
        locations_data = []
        for location in locations:
            location_dict = {
                'filter_id': location['filter_id'],
                'location': location['location']
            }
            locations_data.append(location_dict)
        
        print(f"✅ Read {len(locations_data)} filter locations")
        return locations_data
    
    async def read_filter_positions(self) -> List[Dict[str, Any]]:
        """Read all filter positions from database"""
        print("👷 Reading filter positions...")
        
        positions = await self.conn.fetch("""
            SELECT filter_id, position
            FROM filter_positions
            ORDER BY filter_id, position
        """)
        
        positions_data = []
        for position in positions:
            position_dict = {
                'filter_id': position['filter_id'],
                'position': position['position']
            }
            positions_data.append(position_dict)
        
        print(f"✅ Read {len(positions_data)} filter positions")
        return positions_data
    
    async def read_mutes(self) -> List[Dict[str, Any]]:
        """Read all mutes from database"""
        print("🔇 Reading mutes...")
        
        mutes = await self.conn.fetch("""
            SELECT id, user_id, shift_link, created_at
            FROM mutes
            ORDER BY id
        """)
        
        mutes_data = []
        for mute in mutes:
            mute_dict = {
                'id': mute['id'],
                'user_id': mute['user_id'],
                'shift_link': mute['shift_link'],
                'created_at': mute['created_at'].isoformat()
            }
            mutes_data.append(mute_dict)
        
        print(f"✅ Read {len(mutes_data)} mutes")
        return mutes_data
    
    async def export_to_file(self, output_file: str = None):
        """Export all data to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"database_export_{timestamp}.json"
        
        print(f"📁 Exporting data to {output_file}...")
        
        # Read all data
        users = await self.read_users()
        filters = await self.read_filters()
        companies = await self.read_filter_companies()
        locations = await self.read_filter_locations()
        positions = await self.read_filter_positions()
        mutes = await self.read_mutes()
        
        # Prepare export data
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'users': users,
            'filters': filters,
            'filter_companies': companies,
            'filter_locations': locations,
            'filter_positions': positions,
            'mutes': mutes
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Data exported successfully to {output_file}")
        
        # Show summary
        print(f"\n📊 Export summary:")
        print(f"   👥 Users: {len(users)}")
        print(f"   🔍 Filters: {len(filters)}")
        print(f"   🏢 Companies: {len(companies)}")
        print(f"   📍 Locations: {len(locations)}")
        print(f"   👷 Positions: {len(positions)}")
        print(f"   🔇 Mutes: {len(mutes)}")
        
        return output_file


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Export database data to JSON file')
    parser.add_argument('--output', '-o', help='Output JSON file name')
    parser.add_argument('--database-url', help='Database URL (overrides DATABASE_URL env var)')
    
    args = parser.parse_args()
    
    # Get database URL
    database_url = args.database_url or os.getenv('DATABASE_URL', 'postgresql://tjv:tjv@localhost:5432/tjv')
    
    print("🚀 Starting database data export...")
    print(f"🔗 Database: {database_url}")
    
    reader = DatabaseReader(database_url)
    
    try:
        await reader.connect()
        output_file = await reader.export_to_file(args.output)
        print(f"\n✨ Export completed successfully!")
        print(f"📁 File: {output_file}")
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return 1
    
    finally:
        await reader.disconnect()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
