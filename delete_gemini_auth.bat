@echo off
echo Deleting Gemini authentication files...
del "%USERPROFILE%\.gemini\google_accounts.json"
del "%USERPROFILE%\.gemini\oauth_creds.json"
del "%USERPROFILE%\.gemini\google_account_id"
echo Deletion complete. You can now re-authenticate with the /auth command.