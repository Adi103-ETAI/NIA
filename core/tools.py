"""
Defines the tools (plugins) that the LangChain agent can use.
"""
from langchain.tools import Tool
from plugins.plugin_app_launcher import AppLauncher
from plugins.plugin_file_manager import FileManager

# Initialize our plugin classes
app_launcher = AppLauncher()
file_manager = FileManager()

# Define the tools
app_launcher_tool = Tool(
    name="AppLauncher",
    func=app_launcher.launch_app,
    description="Launches applications on the computer. Use this to open programs like 'chrome', 'spotify', or 'notepad'. The input should be the name of the application."
)

file_search_tool = Tool(
    name="FileSearch",
    func=file_manager.search_files,
    description="Searches for files in a specified directory. The input should be a string containing the directory path and a search query, separated by a comma. For example: 'C:/Users/username/Documents, report.docx'"
)

# A list of all tools that the agent can use
ALL_TOOLS = [app_launcher_tool, file_search_tool]
