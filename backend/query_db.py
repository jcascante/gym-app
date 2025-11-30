#!/usr/bin/env python3
"""
SQLite Database Query Tool for Gym App

Provides easy access to query the local SQLite database with pre-built queries
and custom SQL execution.

Usage:
    python query_db.py                    # Interactive menu
    python query_db.py --users            # List all users
    python query_db.py --clients          # List all clients
    python query_db.py --sql "SELECT ..." # Run custom SQL
"""

import sqlite3
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


# Database file path
DB_PATH = Path(__file__).parent / "gym_app.db"


class DatabaseQuery:
    """Helper class for querying SQLite database."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        if not Path(self.db_path).exists():
            print(f"❌ Database not found at: {self.db_path}")
            print("   Make sure the server has been run at least once to create the database.")
            sys.exit(1)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dictionaries."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            conn.commit()
            return results
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
        finally:
            conn.close()

    def list_users(self):
        """List all users in the database."""
        query = """
            SELECT
                email,
                role,
                is_active,
                password_must_be_changed,
                subscription_id,
                location_id,
                last_login_at,
                created_at
            FROM users
            ORDER BY created_at DESC
        """
        results = self.execute_query(query)

        if not results:
            print("No users found.")
            return

        print(f"\n{'='*100}")
        print(f"{'EMAIL':<35} {'ROLE':<20} {'ACTIVE':<8} {'PWD_CHANGE':<11} {'LAST_LOGIN':<20}")
        print(f"{'='*100}")

        for user in results:
            email = user['email'][:34]
            role = user['role']
            active = '✓' if user['is_active'] else '✗'
            pwd_change = '⚠️ YES' if user['password_must_be_changed'] else 'No'
            last_login = user['last_login_at'][:19] if user['last_login_at'] else 'Never'

            print(f"{email:<35} {role:<20} {active:<8} {pwd_change:<11} {last_login:<20}")

        print(f"{'='*100}")
        print(f"Total users: {len(results)}\n")

    def list_clients(self):
        """List all client users."""
        query = """
            SELECT
                u.email,
                u.is_active,
                u.password_must_be_changed,
                u.profile,
                u.last_login_at,
                u.created_at
            FROM users u
            WHERE u.role = 'CLIENT'
            ORDER BY u.created_at DESC
        """
        results = self.execute_query(query)

        if not results:
            print("No clients found.")
            return

        print(f"\n{'='*100}")
        print(f"{'EMAIL':<35} {'NAME':<25} {'ACTIVE':<8} {'PWD_CHANGE':<11} {'CREATED':<20}")
        print(f"{'='*100}")

        for client in results:
            email = client['email'][:34]

            # Extract name from profile JSON
            profile = client.get('profile', '')
            name = 'N/A'
            if profile and 'basic_info' in str(profile):
                try:
                    import json
                    prof = json.loads(profile) if isinstance(profile, str) else profile
                    basic_info = prof.get('basic_info', {})
                    first = basic_info.get('first_name', '')
                    last = basic_info.get('last_name', '')
                    if first or last:
                        name = f"{first} {last}".strip()
                except:
                    pass

            active = '✓' if client['is_active'] else '✗'
            pwd_change = '⚠️ YES' if client['password_must_be_changed'] else 'No'
            created = client['created_at'][:19] if client['created_at'] else 'Unknown'

            print(f"{email:<35} {name:<25} {active:<8} {pwd_change:<11} {created:<20}")

        print(f"{'='*100}")
        print(f"Total clients: {len(results)}\n")

    def list_coaches(self):
        """List all coach users."""
        query = """
            SELECT
                u.email,
                u.is_active,
                u.profile,
                (SELECT COUNT(*) FROM coach_client_assignments cca
                 WHERE cca.coach_id = u.id AND cca.is_active = 1) as client_count,
                u.created_at
            FROM users u
            WHERE u.role = 'COACH'
            ORDER BY u.created_at DESC
        """
        results = self.execute_query(query)

        if not results:
            print("No coaches found.")
            return

        print(f"\n{'='*90}")
        print(f"{'EMAIL':<35} {'NAME':<25} {'ACTIVE':<8} {'CLIENTS':<10} {'CREATED':<20}")
        print(f"{'='*90}")

        for coach in results:
            email = coach['email'][:34]

            # Extract name from profile JSON
            profile = coach.get('profile', '')
            name = 'N/A'
            if profile:
                try:
                    import json
                    prof = json.loads(profile) if isinstance(profile, str) else profile
                    basic_info = prof.get('basic_info', {})
                    first = basic_info.get('first_name', '')
                    last = basic_info.get('last_name', '')
                    if first or last:
                        name = f"{first} {last}".strip()
                except:
                    pass

            active = '✓' if coach['is_active'] else '✗'
            client_count = coach['client_count']
            created = coach['created_at'][:19] if coach['created_at'] else 'Unknown'

            print(f"{email:<35} {name:<25} {active:<8} {client_count:<10} {created:<20}")

        print(f"{'='*90}")
        print(f"Total coaches: {len(results)}\n")

    def list_subscriptions(self):
        """List all subscriptions."""
        query = """
            SELECT
                name,
                subscription_type,
                status,
                (SELECT COUNT(*) FROM users WHERE users.subscription_id = subscriptions.id) as user_count,
                created_at
            FROM subscriptions
            ORDER BY created_at DESC
        """
        results = self.execute_query(query)

        if not results:
            print("No subscriptions found.")
            return

        print(f"\n{'='*90}")
        print(f"{'NAME':<30} {'TYPE':<15} {'STATUS':<15} {'USERS':<10} {'CREATED':<20}")
        print(f"{'='*90}")

        for sub in results:
            name = sub['name'][:29]
            sub_type = sub['subscription_type']
            status = sub['status']
            users = sub['user_count']
            created = sub['created_at'][:19] if sub['created_at'] else 'Unknown'

            print(f"{name:<30} {sub_type:<15} {status:<15} {users:<10} {created:<20}")

        print(f"{'='*90}")
        print(f"Total subscriptions: {len(results)}\n")

    def list_programs(self):
        """List all training programs."""
        query = """
            SELECT
                p.name,
                p.description,
                p.duration_weeks,
                p.days_per_week,
                p.is_template,
                u.email as created_by_email,
                p.created_at
            FROM programs p
            LEFT JOIN users u ON p.created_by = u.id
            ORDER BY p.created_at DESC
        """
        results = self.execute_query(query)

        if not results:
            print("No programs found.")
            return

        print(f"\n{'='*100}")
        print(f"{'NAME':<30} {'DURATION':<10} {'DAYS/WK':<8} {'TEMPLATE':<10} {'CREATED BY':<25}")
        print(f"{'='*100}")

        for prog in results:
            name = prog['name'][:29]
            duration = f"{prog['duration_weeks']}w"
            days = prog['days_per_week']
            template = '✓' if prog['is_template'] else '✗'
            creator = prog['created_by_email'][:24] if prog['created_by_email'] else 'Unknown'

            print(f"{name:<30} {duration:<10} {days:<8} {template:<10} {creator:<25}")

        print(f"{'='*100}")
        print(f"Total programs: {len(results)}\n")

    def show_user_detail(self, email: str):
        """Show detailed information for a specific user."""
        query = """
            SELECT *
            FROM users
            WHERE email = ?
        """
        results = self.execute_query(query, (email,))

        if not results:
            print(f"User not found: {email}")
            return

        user = results[0]

        print(f"\n{'='*80}")
        print(f"USER DETAILS: {email}")
        print(f"{'='*80}")
        print(f"ID:                     {user['id']}")
        print(f"Email:                  {user['email']}")
        print(f"Role:                   {user['role']}")
        print(f"Active:                 {'Yes' if user['is_active'] else 'No'}")
        print(f"Password Must Change:   {'⚠️  YES' if user['password_must_be_changed'] else 'No'}")
        print(f"Subscription ID:        {user['subscription_id'] or 'None'}")
        print(f"Location ID:            {user['location_id'] or 'None'}")
        print(f"Last Login:             {user['last_login_at'] or 'Never'}")
        print(f"Created At:             {user['created_at']}")
        print(f"Updated At:             {user['updated_at']}")
        print(f"\nProfile:")
        if user['profile']:
            try:
                import json
                profile = json.loads(user['profile']) if isinstance(user['profile'], str) else user['profile']
                print(json.dumps(profile, indent=2))
            except:
                print(user['profile'])
        else:
            print("  No profile data")
        print(f"{'='*80}\n")

    def list_tables(self):
        """List all tables in the database."""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """
        results = self.execute_query(query)

        print(f"\n{'='*50}")
        print("DATABASE TABLES")
        print(f"{'='*50}")
        for table in results:
            print(f"  - {table['name']}")
        print(f"{'='*50}\n")

    def custom_query(self, sql: str):
        """Execute a custom SQL query."""
        results = self.execute_query(sql)

        if not results:
            print("Query returned no results (or failed).")
            return

        # Print results as table
        if results:
            # Get column names
            columns = list(results[0].keys())

            # Calculate column widths
            col_widths = {col: len(col) for col in columns}
            for row in results:
                for col in columns:
                    col_widths[col] = max(col_widths[col], len(str(row[col])))

            # Print header
            total_width = sum(col_widths.values()) + len(columns) * 3 + 1
            print(f"\n{'='*total_width}")
            header = " | ".join([col.upper().ljust(col_widths[col]) for col in columns])
            print(header)
            print(f"{'='*total_width}")

            # Print rows
            for row in results:
                row_str = " | ".join([str(row[col]).ljust(col_widths[col]) for col in columns])
                print(row_str)

            print(f"{'='*total_width}")
            print(f"Total rows: {len(results)}\n")


def main():
    parser = argparse.ArgumentParser(description="Query Gym App SQLite Database")
    parser.add_argument('--users', action='store_true', help='List all users')
    parser.add_argument('--clients', action='store_true', help='List all clients')
    parser.add_argument('--coaches', action='store_true', help='List all coaches')
    parser.add_argument('--subscriptions', action='store_true', help='List all subscriptions')
    parser.add_argument('--programs', action='store_true', help='List all programs')
    parser.add_argument('--tables', action='store_true', help='List all database tables')
    parser.add_argument('--user', type=str, help='Show details for specific user email')
    parser.add_argument('--sql', type=str, help='Execute custom SQL query')
    parser.add_argument('--db', type=str, help='Path to database file (default: ./gym_app.db)')

    args = parser.parse_args()

    # Initialize database query helper
    db = DatabaseQuery(args.db)

    # If specific query requested, execute it
    if args.users:
        db.list_users()
    elif args.clients:
        db.list_clients()
    elif args.coaches:
        db.list_coaches()
    elif args.subscriptions:
        db.list_subscriptions()
    elif args.programs:
        db.list_programs()
    elif args.tables:
        db.list_tables()
    elif args.user:
        db.show_user_detail(args.user)
    elif args.sql:
        db.custom_query(args.sql)
    else:
        # Interactive menu
        show_menu(db)


def show_menu(db: DatabaseQuery):
    """Show interactive menu."""
    while True:
        print("\n" + "="*60)
        print("GYM APP DATABASE QUERY TOOL")
        print("="*60)
        print("1. List all users")
        print("2. List all clients")
        print("3. List all coaches")
        print("4. List all subscriptions")
        print("5. List all programs")
        print("6. List database tables")
        print("7. Show user details (by email)")
        print("8. Execute custom SQL query")
        print("9. Exit")
        print("="*60)

        choice = input("\nEnter your choice (1-9): ").strip()

        if choice == '1':
            db.list_users()
        elif choice == '2':
            db.list_clients()
        elif choice == '3':
            db.list_coaches()
        elif choice == '4':
            db.list_subscriptions()
        elif choice == '5':
            db.list_programs()
        elif choice == '6':
            db.list_tables()
        elif choice == '7':
            email = input("Enter user email: ").strip()
            db.show_user_detail(email)
        elif choice == '8':
            print("\nEnter SQL query (press Enter twice to execute):")
            lines = []
            while True:
                line = input()
                if line == '':
                    break
                lines.append(line)
            sql = ' '.join(lines)
            if sql:
                db.custom_query(sql)
        elif choice == '9':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
