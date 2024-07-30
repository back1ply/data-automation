from pykeepass import PyKeePass

def get_credentials(database_path, entry_title):
    # Prompt for the KeePass database master password
    master_password = "ThisIs@JoelTing.com"

    try:
        # Open the KeePass database
        kp = PyKeePass(database_path, password=master_password)

        # Find the entry by its title
        entry = kp.find_entries(title=entry_title, first=True)

        if entry:
            username = entry.username
            password = entry.password
            client = entry.custom_properties["client"]
            sys = entry.custom_properties["system"]
            return username, password, client, sys
        else:
            print(f"Entry '{entry_title}' not found in the KeePass database.")
            return None, None

    except Exception as e:
        print(f"Error accessing KeePass database: {str(e)}")
        return None, None