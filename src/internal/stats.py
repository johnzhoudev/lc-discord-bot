import asyncio
from collections import defaultdict
import logging
from pydantic import BaseModel
from typing import Dict

log = logging.getLogger(__name__)

QUESTION_COMPLETE_EMOJIS = ["✅"]


class UserStats(BaseModel):
    user_name: str
    total_completed: int
    streak: int

    reactions: Dict[int, set[str]] = defaultdict(set)  # Post id to reactions list

    def is_question_complete(self, post_id: int):
        for emoji in QUESTION_COMPLETE_EMOJIS:
            if emoji in self.reactions[post_id]:
                return True
        return False


class StatsManager:
    _users: Dict[str, UserStats] = {}
    _state_lock = asyncio.Lock()

    _post_ids: set[int] = set()  # Track post ids

    _users_who_completed_streak = set()
    _current_post_id = None

    # MUST BE CALLED holding lock!
    def _get_user(self, user_name: str):
        if user_name in self._users:
            return self._users[user_name]

        res = UserStats(user_name=user_name, total_completed=0, streak=0)
        self._users[user_name] = res
        return res

    async def init(self, members: list[str]):
        for member in members:
            _ = self._get_user(member)
            log.info(f"Added user: {member}")

    async def log_user_reaction_remove(self, user_name: str, post_id: int, emoji: str):
        async with self._state_lock:
            if post_id not in self._post_ids:
                return

            user_stats = self._get_user(user_name)

            # If question is complete and is no longer complete, adjust sums
            user_stats.reactions[post_id].remove(emoji)

            if not user_stats.is_question_complete(post_id):
                user_stats.total_completed -= 1

                if self._current_post_id == post_id:
                    self._users_who_completed_streak.remove(user_name)
                    user_stats.streak -= 1

                log.info(
                    f"{user_name} question complete undone, total count: {user_stats.total_completed} streak: {user_stats.streak}"
                )

    async def log_user_reaction_add(self, user_name: str, post_id: int, emoji: str):
        async with self._state_lock:
            if post_id not in self._post_ids:
                return

            user_stats = self._get_user(user_name)

            if (
                not user_stats.is_question_complete(post_id)
                and emoji in QUESTION_COMPLETE_EMOJIS
            ):
                # New question complete!
                user_stats.total_completed += 1

                if self._current_post_id == post_id:
                    self._users_who_completed_streak.add(user_name)
                    user_stats.streak += 1

                log.info(
                    f"{user_name} completed a question! total count: {user_stats.total_completed} streak: {user_stats.streak}"
                )

            user_stats.reactions[post_id].add(emoji)

    async def handle_new_post(self, post_id: int):
        """
        Resets streaks!
        """
        async with self._state_lock:
            self._current_post_id = post_id
            self._post_ids.add(post_id)

            for user, stats in self._users.items():
                if user not in self._users_who_completed_streak and stats.streak != 0:
                    log.info(f"{user} lost their streak!")  # TODO: Send to channel?
                    self._users[user].streak = 0

            self._users_who_completed_streak.clear()

    async def get_user_stats(self):  # returns copies of user stats
        """
        Returns copies of user stats
        """
        res = []
        async with self._state_lock:
            for stats in self._users.values():
                res.append(stats.model_copy())
        return res
