# friends_tool.py
from ibm_watsonx_orchestrate.agent_builder.tools import tool
import random


# List of Indian friends names
FRIENDS_LIST = [
    "Aarav",
    "Vivaan", 
    "Aditya",
    "Vihaan",
    "Arjun",
    "Sai",
    "Reyansh",
    "Ayaan",
    "Krishna",
    "Ishaan",
    "Shaurya",
    "Atharv",
    "Advik",
    "Pranav",
    "Rudra",
    "Priya",
    "Ananya",
    "Kavya",
    "Aanya",
    "Diya",
    "Sara",
    "Myra",
    "Aara",
    "Zara",
    "Navya",
    "Aadhya",
    "Arya",
    "Khushi",
    "Anvi",
    "Riya"
]


@tool()
def get_friends_info(query: str) -> str:
    """Get information about my friends list or return friend names.

    Args:
        query (str): The query about friends - can be "all", "random", "count", or search for specific name.

    Returns:
        str: Information about friends based on the query.
    """
    
    query_lower = query.lower().strip()
    
    if query_lower in ["all", "list", "show all", "all friends"]:
        return f"Here are all my friends: {', '.join(FRIENDS_LIST)}"
    
    elif query_lower in ["random", "random friend", "pick one"]:
        random_friend = random.choice(FRIENDS_LIST)
        return f"Random friend: {random_friend}"
    
    elif query_lower in ["count", "how many", "total"]:
        return f"I have {len(FRIENDS_LIST)} friends in my list."
    
    elif query_lower in ["help", "what can you do"]:
        return ("I can help you with friends information. Try asking: "
                "'all friends', 'random friend', 'count friends', or search for a specific name.")
    
    else:
        # Search for a specific friend name
        matching_friends = [friend for friend in FRIENDS_LIST if query_lower in friend.lower()]
        
        if matching_friends:
            return f"Found matching friends: {', '.join(matching_friends)}"
        else:
            return f"No friend found matching '{query}'. Try 'all friends' to see the complete list."