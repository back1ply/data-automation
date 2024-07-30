import os
import logging
import win32com.client as win32
from . import systemfx
from . import keepass

# Get the logger
logger = logging.getLogger("functions")

systemfx.clear_gen_path()

def get_afo_credentials(keepass_db):
    try:
        user, pwd, client, sys = keepass.get_credentials(keepass_db, "SAP AFO")
        return user, pwd, client, sys
    except Exception as e:
        logger.error(f"Error loading SAP AFO credentials. Error: {e}")
        return e

def process_sap_excel_varyearperiod(sap_afo_excel_file, secret_filepath, year, period):
    try:
        # Create a new directory if it doesn't exist
        new_directory = systemfx.check_and_create_directory(sap_afo_excel_file)
        new_directory = new_directory + "\\"

        # Concatenate year and period to form a string
        YearPeriod = str(year) + str.format('{:02d}', period)
        filenameYearPeriod = f"{year}{period:02d}"

        # Start Excel application and configure settings
        excel_instance = win32.gencache.EnsureDispatch('Excel.Application')
        excel_instance.Visible = True
        excel_instance.DisplayAlerts = False

        # Open specified workbook and enable AFO Add-in
        workbook_sap = excel_instance.Workbooks.Open(sap_afo_excel_file, False, False)
        excel_instance.COMAddIns("SapExcelAddIn").Connect = False
        excel_instance.COMAddIns("SapExcelAddIn").Connect = True  
        logger.info("AFO Add-in enabled.")

        # Close workbook again, as sometimes, if it is the addin is enabled with the workbook opened, it will not run SAP macros
        workbook_sap.Close()

        # Reopen to make sure SAP macros can run without error
        workbook_sap = excel_instance.Workbooks.Open(sap_afo_excel_file, False, False)
        logger.info(f"AFO workbook {sap_afo_excel_file} opened.")
                
        # Login to SAP AFO
        user, pwd, client, _ = get_afo_credentials(secret_filepath)
        workbook_sap.Application.Run("SAPLogon", "DS_1", client, user, pwd)

        # Refresh Data
        logger.info("Data Refreshing...")
        workbook_sap.Application.Run("SAPExecuteCommand", "Refresh")
        
        # Configure refresh behavior and submit variables
        workbook_sap.Application.Run("SAPSetRefreshBehaviour", "Off")
        workbook_sap.Application.Run("SAPExecuteCommand", "PauseVariableSubmit", "On")

        # Set variable and submit
        workbook_sap.Application.Run("SAPSetVariable", "ZVAR_YRPRD", YearPeriod, "INPUT_STRING", "DS_1")
        workbook_sap.Application.Run("SAPExecuteCommand", "PauseVariableSubmit", "Off")
        workbook_sap.Application.Run("SAPSetRefreshBehaviour", "On")

        # Set Filter, Filter needs to be done after refresh
        # workbook_sap.Application.Run("SAPSetFilter", "DS_1", "<Technical name of field>", "<filter criteria>", "INPUT_STRING")
        logger.info("Data Refresh Completed...")

        # determine new file name
        original_filename = os.path.splitext(os.path.basename(sap_afo_excel_file))[0]
        file_extension = os.path.splitext(sap_afo_excel_file)[1]
        new_filename = f"{original_filename} {filenameYearPeriod}{file_extension}"
        new_file_path = os.path.join(new_directory, new_filename)

        # Save and close the workbook
        systemfx.remove_file_if_exists(new_file_path)
        workbook_sap.SaveAs(new_file_path)
        workbook_sap.Saved = True
        workbook_sap.Close()
        excel_instance.Quit()

        logger.info(f"AFO workbook file refreshed and saved as {new_file_path}")
        return new_file_path

    except Exception as e:
        logger.error(f"Failed to refresh {sap_afo_excel_file}. Error: {e}")
        return e
