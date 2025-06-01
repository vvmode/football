import os
import psycopg2
from typing import List, Set, Tuple
from dotenv import load_dotenv

class TeamManager:
    def __init__(self):
        self.super_admin_ids: Set[int] = set()
        self.super_admin_usernames: Set[str] = {"Xellision"}
        self.admin_usernames: Set[str] = set()
       
        self.main_team: List[Tuple[int, str, str]] = []
        self.reserve_team: List[Tuple[int, str, str]] = []
        self.max_players: int = 20
        self.venue: str = "Not Set"
        self.event_date: str = "Not Set"
       # Load admin users from DB
        self.load_admin_users_from_db()
        
    def set_super_admin(self, user_id: int, username: str = None):
        self.super_admin_ids.add(user_id)
        if username:
            self.super_admin_usernames.add(username)
        self.admin_ids.add(user_id)
        

    def remove_admin(self, user_id: int):
        # Prevent removal if user is a super admin
        if user_id not in self.super_admin_ids:
            self.admin_ids.discard(user_id)
    
    def load_admin_users_from_db(self):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                sslmode="require"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM admin_users")
            rows = cursor.fetchall()

            for user_id, username in rows:
              
                if username:
                    self.admin_usernames.add(username)

            cursor.close()
            conn.close()
        except Exception as e:
            print(f"❌ Failed to load admin users: {e}")

    def store_admin_user_to_db(self, username: str):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
                sslmode="require"
            )
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO admin_users (username)
                VALUES (%s)
                ON CONFLICT (username) DO UPDATE
                SET username = EXCLUDED.username
            """, (username,))

            conn.commit()
            cursor.close()
            conn.close()

        # Add to in-memory sets as well
            if username:
                self.admin_usernames.add(username)

            print(f"✅ Admin user {username} stored successfully.")
        except Exception as e:
            print(f"❌ Failed to store admin user: {e}")


        
    def is_admin(self, username: str = None) -> bool:
        return (username is not None and username in self.admin_usernames
        )

    def is_super_admin(self, user_id: int = None, username: str = None) -> bool:
        return (
            (user_id is not None and user_id in self.super_admin_ids)
            or (username is not None and username in self.super_admin_usernames)
        )

    def set_event_details(self, max_players: int, venue: str, event_date: str):
        self.max_players = max_players
        self.venue = venue
        self.event_date = event_date

    def clear_teams(self):
        self.main_team.clear()
        self.reserve_team.clear()

    def join_team(self, user_id: int, full_name: str, username: str) -> str:
        if any(user_id == uid for uid, _, _ in self.main_team + self.reserve_team):
            return "⚠️ You're already in the team or reserve list."

        entry = (user_id, full_name, username)

        if len(self.main_team) < self.max_players:
            self.main_team.append(entry)
            return "✅ You've been added to the main team!"
        else:
            self.reserve_team.append(entry)
            return "🕒 Main team full. You've been added to the reserve list."

    def leave_team(self, user_id: int) -> str:
        for team in [self.main_team, self.reserve_team]:
            for i, (uid, _, _) in enumerate(team):
                if uid == user_id:
                    team.pop(i)
                    if team is self.main_team and self.reserve_team:
                        promoted = self.reserve_team.pop(0)
                        self.main_team.append(promoted)
                        return f"👋 You left. {promoted[1]} (@{promoted[2]}) promoted from reserve list."
                    return "👋 You've left the team."
        return "❌ You're not in any list."

    def format_team_list(self) -> str:
        lines = ["👥 <b>Current Team Members:</b>"]
        for i, (_, name, username) in enumerate(self.main_team, 1):
            lines.append(f"{i} {name} (@{username})")
        if not self.main_team:
            lines.append("No team members yet.")

        if self.reserve_team:
            lines.append("\n🕒 <b>Reserve List:</b>")
            for i, (_, name, username) in enumerate(self.reserve_team, 1):
                lines.append(f"{i}. {name} (@{username})")
        return "\n".join(lines)
