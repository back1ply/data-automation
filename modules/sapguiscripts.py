# Importing the Libraries
import win32com.client
from pathlib import Path
import subprocess
import time
import win32ui
import logging
from . import keepass
from . import systemfx

logger = logging.getLogger("functions")

def get_sap_credentials(keepass_db):
    try:
        user, pwd, client, sys = keepass.get_credentials(keepass_db, "SAP GUI")
        return user, pwd, client, sys
    except Exception as e:
        logger.error(f"Error loading SAP GUI credentials. Error: {e}")
        return e

def get_sap_connection(keepass_db):
    try:
        logger.info(f"Connecting to SAP GUI")
        # Attempt to get the SAP connection
        SapGuiAuto = win32com.client.GetObject('SAPGUI')
        objGUI = SapGuiAuto.GetScriptingEngine
        objConn = objGUI.Children(0)
        logger.info(f"SAP connection found")
        session = objConn.Children(0)
        return session
    except Exception as e:
        logger.info(f"Could not find SAP connection, attempting to start a new one")
        user, pwd, client, sys = get_sap_credentials(keepass_db)
        # If the connection is not found, start a new one"SAP connection found"
        session = start_sap(user, pwd, client, sys)
        return session

def start_sap(user, pwd, client, sys):

    command = ['C:\Program Files (x86)\SAP\FrontEnd\SAPgui\sapshcut.exe',f'-system={sys}', f'-client={client}', f'-user={user}', f'-pw={pwd}', '-language=en']
    subprocess.check_call(command)
    
    # Window title to search for
    window_title = f"SAP Easy Access  -  User Menu for {user}"

    # Loop until the window is found
    while True:
        try:
            # Find the window with the specified title
            hwnd = win32ui.FindWindow(None, window_title)
            if hwnd:
                print(f"Found window: {window_title}")
                break
        except win32ui.error:
            pass
        # Sleep for 1 second before trying again
        time.sleep(1)

    SapGuiAuto = win32com.client.GetObject('SAPGUI')
    objGUI = SapGuiAuto.GetScriptingEngine
    objConn = objGUI.Children(0)
    session = objConn.Children(0)    

    return session

def f08extract(year, period, keepass_db, output_dir):
    session = get_sap_connection(keepass_db)
    logger.info(f"Extracting Trial Balance from F.08")
    new_file_path = Path(output_dir) / f"TB {year}{period:02d}.txt"
    session.findById("wnd[0]/tbar[0]/okcd").text = "/nf.08"
    session.findById("wnd[0]").sendVKey(0)
    session.findById("wnd[0]/usr/chkPAR_LIS2").selected = False
    session.findById("wnd[0]/usr/ctxtSD_BUKRS-LOW").text = "1710"
    session.findById("wnd[0]/usr/txtSD_GJAHR-LOW").text = str(year)
    session.findById("wnd[0]/usr/txtB_MONATE-LOW").text = "1"
    session.findById("wnd[0]/usr/txtB_MONATE-HIGH").text = str(period)
    session.findById("wnd[0]").sendVKey(8)
    session.findById("wnd[0]/mbar/menu[3]/menu[5]/menu[2]/menu[2]").select()
    session.findById("wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]").select()
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    systemfx.remove_file_if_exists(new_file_path)
    session.findById("wnd[1]/usr/ctxtDY_PATH").text = output_dir
    session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = f"TB { year}{period:02d}.txt"
    session.findById("wnd[1]/tbar[0]/btn[0]").press()
    logger.info(f"{new_file_path} exported...")
    return new_file_path

