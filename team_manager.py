from typing import List, Set, Tuple

class TeamManager:
    def __init__(self):
        self.super_admin_id = None
        self.super_admin_usernames: Set[str] = {"vvmode", "Xellision"}  # Hardcoded super admins
        self.admin_ids: Set[int] = set()
        self.main_team: List[Tuple[int, str, str]] = []
        self.reserve_team: List[Tuple[int, str, str]] = []
        self.max_players: int = 20
        self.venue: str = "Not Set"
        self.event_date: str = "Not Set"

    def add_super_admin(self, user_id: int = None, username: str = None):
        if user_id is not None:
            self.super_admin_ids.add(user_id)
            self.admin_ids.add(user_id)
        if username is not None:
            self.super_admin_usernames.add(username)

    def remove_super_admin(self, user_id: int = None, username: str = None):
        if user_id is not None:
            self.super_admin_ids.discard(user_id)
        if username is not None and username not in {"vvmode", "Xellision"}:
            self.super_admin_usernames.discard(username)

    def remove_admin(self, user_id: int):
        if user_id != self.super_admin_id:
            self.admin_ids.discard(user_id)

    def is_admin(self, user_id: int = None, username: str = None) -> bool:
        return (
            (user_id is not None and user_id in self.admin_ids)
            or (username is not None and username == self.super_admin_username)
        )

    def is_super_admin(self, user_id: int = None, username: str = None) -> bool:
        return (
            (user_id is not None and user_id == self.super_admin_id)
            or (username is not None and username == self.super_admin_username)
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
