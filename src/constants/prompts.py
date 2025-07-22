STORY_GENERATION_SYSTEM_PROMPT = """
You are a story generator assistant for a discord bot that posts leetcode questions. The discord bot will 
have 'campaigns' where a series of questions will be posted, each accompanied by a small story blurb continuing
the story with each question. 

The stories you generate should be:

1. 1 paragraph long, or 6 sentences max. 
2. Follow a narrative structure: (exposition, rising action, climax, falling action, and resolution) over the course of the campaign, with a central plot established in the introduction.
3. Loosely related to the leetcode question provided.
4. Following the campaign instructions / theme provided by the user.
5. Each section should connect with the previous section in a continuous story.
6. Each section should end in an "ask" where the characters in the story need to solve a problem related to the leetcode question provided. Ie, will the characters finish the task in time?
7. Subsequent sections should start by addressing if the characters succeeded the previous story's "ask" or not.

"""

USER_STORY_SETUP_PROMPT_DEFAULT = """
Campaign instructions and theme: Choose a random campaign setting. Try NOT to be stereotypical. Make it exciting, with some stakes,
and the occasional twist and turn.
"""

USER_STORY_SETUP_PROMPT_TEMPLATE = """
Campaign instructions and theme: {}
"""

STORY_HISTORY_PROMPT_TEMPLATE = """
The story so far: 

{}
"""

STORY_GENERATION_KICKSTART_PROMPT = """
Here is the leetcode question description you should base this next part on:
{}

Now, write part {} of {} total parts of the story:
"""
UNLIMITED_STORY_KICKSTART_PROMPT = """
Here is the leetcode question description you should base this next part on:
{}

This story never ends. Now, write the next part the story:
"""


def get_story_generation_kickstart_prompt(
    question_desc: str, part: int, total_parts: int
):
    if total_parts == -1:  # unlimited
        return UNLIMITED_STORY_KICKSTART_PROMPT.format(question_desc)

    return STORY_GENERATION_KICKSTART_PROMPT.format(question_desc, part, total_parts)
