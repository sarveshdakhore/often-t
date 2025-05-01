# Often MCP Server

This is a Model Control Protocol (MCP) server for the Often travel planning system. It provides various tools for Claude AI to access travel planning functionality, including destinations, activities, hotels, and itinerary creation.

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Claude for Desktop (latest version)

## Installation

1. Clone this repository or ensure you have all the required files in your project directory.

2. Set up your Python environment using uv:

```bash
cd /Users/sarveshdakhore/Desktop/often-t
uv venv
```

3. Activate the virtual environment:

```bash
# For macOS/Linux
source .venv/bin/activate

# For Windows
.venv\Scripts\activate
```

4. Install dependencies (choose one method):

   **Option 1: Direct installation**
   ```bash
   uv pip install fastmcp httpx sqlalchemy
   # Install any other required dependencies for your project
   ```

   **Option 2: Using requirements.txt**

   Install from requirements.txt:
   ```bash
   uv pip install -r requirements.txt
   ```

## Configure Claude for Desktop

1. Make sure you have Claude for Desktop installed. If not, download and install the latest version.

2. Open or create the Claude for Desktop configuration file:

```bash
# For macOS
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

3. Add your Often MCP server configuration:

```json
{
    "mcpServers": {
        "often": {
            "command": "uv",
            "args": [
                "--directory",
                "/Users/sarveshdakhore/Desktop/often-t",
                "run",
                "python",
                "mcp_server.py"
            ]
        }
    }
}
```

If needed, use the full path to the uv executable (find it using `which uv`).

4. Save the configuration file and restart Claude for Desktop.

## Running the Server

The server will be automatically started by Claude for Desktop when needed. However, if you want to test it manually:

```bash
cd /Users/sarveshdakhore/Desktop/often-t
uv run python mcp_server.py
```

## Available Tools

Once configured correctly, Claude will have access to the following tools:

- `get_destinations`: Retrieves all available travel destinations
- `get_locations_by_destination`: Gets locations within a destination
- `get_activities_by_location`: Lists activities available at a location
- `get_hotels_by_location`: Lists hotels available at a location
- `get_transport_modes`: Retrieves all available transport modes
- `create_custom_itinerary`: Creates a new custom travel itinerary
- `create_custom_itinerary_from_dict`: Creates an itinerary from a dictionary
- `get_recommended_itinerary`: Generates an itinerary based on a template
- `get_template_as_itinerary`: Retrieves a template in itinerary format

## Testing the Connection

1. Open Claude for Desktop
2. Look for the hammer icon in the UI, which indicates available tools
3. Click on the hammer icon to see the list of tools from your Often server
4. Test with a simple query, such as: "What travel destinations are available?"

## Troubleshooting

If the hammer icon doesn't appear or tools aren't working:

1. Check that the configuration file has the correct paths
2. Verify that all dependencies are installed
3. Look for error messages in Claude for Desktop
4. Try running the server manually to check for errors:
   ```bash
   cd /Users/sarveshdakhore/Desktop/often-t
   uv run python mcp_server.py
   ```
5. Ensure the database and any external APIs your server relies on are accessible

## Database Configuration

Make sure your database connection is properly configured. The MCP server depends on database access to retrieve travel information.

## API Access

Some functions require API access to external services. Ensure all necessary API keys and endpoints are properly configured in your environment.
