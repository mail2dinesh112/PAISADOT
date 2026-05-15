################################################
# Author                : DINESHKUMAR A
# Created Date          : 09th MAY, 2026
# Last Date Modified    : 09th MAY, 2026
# Last Modified By      : DINESHKUMAR A
# Description           : This is the main file which will run the application.
################################################

# IMPORT PACKAGES 
import os
import uvicorn
from dotenv import load_dotenv

if __name__=="__main__":
    try:
        load_dotenv()
        environ =os.getenv("APP_ENV")
        port = os.getenv("APP_PORT")

        print(f"ENVIRONMENT : {environ} , PORT : {port}")
        uvicorn.run(
            "api.common.router:app",
            host="0.0.0.0", 
            port=int(port),  
            reload=True,
            proxy_headers=True,
            forwarded_allow_ips="*"
    )

    except Exception as Error:
        print(f"Exception In Main Function : {Error}")
