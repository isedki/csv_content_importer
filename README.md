
What this script does:

- Reads the Excel file
- Groups rows by blog_post_id (combining de/fr into one entry)
- Creates entries with proper localization (one entry, multiple locales) (german is the default language and it should be configured as such in hygraph)
- Performs an html to slate transformation
- Shows progress and success/error counts

=========================================================================================================
Setup Instructions:

- Delete existing Blog entries in Hygraph UI first
- Get your Hygraph credentials:

Go to Project Settings → API Access
- Copy the Content API endpoint (e.g., https://api-eu-central-1.hygraph.com/v2/xxx/master)
- Create a Permanent Auth Token with Create/Update permissions for Blog model

Edit the script - Update these lines at the top:

HYGRAPH_ENDPOINT = "https://api-eu-central-1.hygraph.com/v2/YOUR_PROJECT/master"
HYGRAPH_TOKEN = "your-permanent-auth-token"
BATCH_SIZE = 5  # Change to None for all 575 entries

Install dependencies:

   pip install pandas requests beautifulsoup4 openpyxl

Run the script:

   python hygraph_batch_import.py

