from mcp.server.fastmcp import FastMCP  # Import FastMCP to create MCP server
import math  # Import Python's math module for factorial calculation
import sys

# Create the MCP server instance and give it a name
mcp = FastMCP("math-tools-mcp")

# Uplift Python's big-int to string safety cap
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1000000)

# -----------------------------------
# Helper function (not a tool)
# ------------------------------------

def compute_factorial(n: int) -> int:
    """
    Return n! as an integer.
    This is a shared helper for both MCP tools below.
    """
    # Check that n is a non-negative integer
    if not isinstance(n, int) or n < 0:
        raise ValueError("n must be a non-negative integer")

    # Use Python's built-in factorial function
    return math.factorial(n)


# ----------------------------
# MCP Tool 1: factorial_value
# ----------------------------

@mcp.tool("factorial_value")
async def factorial_value(n: int) -> int:
    """
    Return the exact value of n! (factorial of n).
    Example:
        factorial_value(5) -> 120
    """

    # Use the helper function to compute the factorial
    return compute_factorial(n)

# ----------------------------
# MCP Tool 2: factorial_digits
# ----------------------------
@mcp.tool("factorial_digits")
async def factorial_digits(n: int) -> int:
    """
    Return the number of digits in n! (factorial of n).
    Example:
        factorial_digits(5) -> 3
    """
    # Get the factorial using the same helper function
    fact_value = compute_factorial(n)

    # Convert to string and count how many characters (digits) it has
    return len(str(fact_value))


# --------------------------------
# Start MCP server if run directly
# --------------------------------
if __name__ == "__main__":
    # Start the MCP server so the MCP tools can be called by watsonx Orchestrate or any LLM.
    mcp.run()