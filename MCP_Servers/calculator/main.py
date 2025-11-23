#!/usr/bin/env python3
"""
Simple Calculator MCP Server
"""

import math
from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Simple Calculator")


@mcp.tool("calculate")
def calculate(expression: str) -> dict:
    """
    Calculate basic math expressions.
    
    Args:
        expression: Math expression like "2 + 3 * 4"
    
    Returns:
        Result of calculation
    """
    try:
        # Safe evaluation with basic math only
        allowed = {
            "abs": abs, "round": round, "min": min, "max": max,
            "pow": pow, "sqrt": math.sqrt, "sin": math.sin, 
            "cos": math.cos, "pi": math.pi, "e": math.e
        }
        
        result = eval(expression, {"__builtins__": {}}, allowed)
        
        return {
            "expression": expression,
            "result": result,
            "success": True
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e),
            "success": False
        }


@mcp.tool("temperature_converter")
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convert temperature between Celsius, Fahrenheit, and Kelvin.
    
    Args:
        value: Temperature value to convert
        from_unit: Source unit (celsius, fahrenheit, kelvin)
        to_unit: Target unit (celsius, fahrenheit, kelvin)
    
    Returns:
        Converted temperature
    """
    try:
        # Convert to Celsius first
        if from_unit.lower() == "fahrenheit":
            celsius = (value - 32) * 5/9
        elif from_unit.lower() == "kelvin":
            celsius = value - 273.15
        else:  # celsius
            celsius = value
        
        # Convert from Celsius to target
        if to_unit.lower() == "fahrenheit":
            result = (celsius * 9/5) + 32
        elif to_unit.lower() == "kelvin":
            result = celsius + 273.15
        else:  # celsius
            result = celsius
        
        return {
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "result": round(result, 2),
            "success": True
        }
    except Exception as e:
        return {
            "original_value": value,
            "from_unit": from_unit,
            "to_unit": to_unit,
            "error": str(e),
            "success": False
        }


@mcp.tool("circle_area_and_circumference")
def circle_area(radius: float) -> dict:
    """
    Calculate area and circumference of a circle.
    
    Args:
        radius: Radius of the circle
    
    Returns:
        Area and circumference
    """
    try:
        area = math.pi * radius * radius
        circumference = 2 * math.pi * radius
        
        return {
            "radius": radius,
            "area": round(area, 2),
            "circumference": round(circumference, 2),
            "success": True
        }
    except Exception as e:
        return {
            "radius": radius,
            "error": str(e),
            "success": False
        }


def main():
    """Main function for running the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()