"""Module to lauch server with specific settings
More info: https://www.uvicorn.org/deployment/
"""

import uvicorn

# Parse commandline arguments and create the settings instance
from launch_setup import settings

def main():
    """Main method to start server"""
    print("SEPIA STT Server - Starting...")
    uvicorn.run("server:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=settings.code_reload)

# Run if this is called as main
if __name__ == "__main__":
    main()
