"""
Tool registry — imports and registers all tool modules with the MCP server.
Adds new tool modules here as you build them. Includes fault-tolerant loading.
"""

import logging

logger = logging.getLogger("friday.tools")

def register_all_tools(mcp):
    """Register all tool groups onto the MCP server instance safely."""
    modules = ["web", "system", "utils", "lab", "memory", "dashboard"]
    loaded = []
    failed = []

    for mod_name in modules:
        try:
            # Dynamic import
            mod = __import__(f"friday.tools.{mod_name}", fromlist=["register"])
            mod.register(mcp)
            loaded.append(mod_name)
        except Exception as e:
            failed.append((mod_name, str(e)))
            logger.error("Failed to load tool module '%s': %s", mod_name, e)

    # Print startup summary
    print("\n" + "="*40)
    print("FRIDAY ARMOR SYSTEMS INITIALIZING")
    print("="*40)
    print(f"Modules Loaded: {', '.join(loaded) if loaded else 'None'}")
    if failed:
        print(f"Modules Failed: {len(failed)}")
        for name, err in failed:
            print(f"  - {name} ({err})")
    print("="*40 + "\n")

