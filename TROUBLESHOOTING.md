# Troubleshooting Guide

## Store ID Required Error

If you're getting asked for a "store ID" when creating OAuth credentials, you've selected the wrong application type.

### Solution:

1. **Go back to Google Cloud Console** > "APIs & Services" > "Credentials"
2. **Delete the existing OAuth 2.0 client** (if you created one)
3. **Create new credentials** with these exact steps:
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - **Choose "Desktop application"** (NOT Android, NOT iOS, NOT Web application)
   - Give it a name like "Gmail CSV Exporter"
   - Click "Create"
   - Download the JSON file and rename to `credentials.json`

### Why this happens:
- Store IDs are only required for **Android** and **iOS** applications
- **Desktop applications** don't need store IDs
- If you accidentally selected Android/iOS, Google assumes you're publishing to app stores

## OAuth Consent Screen Testing Mode Error

If you see: *"This app hasn't been verified by Google yet"* or *"The app is currently being tested"*

### Solution:

1. **Go to Google Cloud Console** > "APIs & Services" > "OAuth consent screen"
2. **Add your email as a test user:**
   - Scroll down to "Test users" section
   - Click "Add Users"
   - Enter your Gmail address
   - Click "Save"
3. **Make sure you're using the correct Google account** (the one you added as test user)
4. **Try the authentication again**

### Alternative: Publish the App (Recommended)

To avoid the testing mode entirely:

1. **Go to OAuth consent screen**
2. **Click "Publish App"** (at the top)
3. **Choose "In production"**
4. **Save changes**
5. **Wait a few minutes** for changes to propagate

**Note:** Publishing makes the app available to all users, but since this is a personal tool, it's safe to publish.

## OAuth Consent Screen Not Configured

If you get an error about OAuth consent screen:

### Solution:

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **"External"** user type
3. Fill in the required information:
   - **App name**: "Gmail CSV Exporter"
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click **"Save and Continue"**
5. On the **Scopes** page, click **"Add or Remove Scopes"**
6. Add this scope: `https://www.googleapis.com/auth/gmail.readonly`
7. Click **"Save and Continue"**
8. On the **Test users** page, add your Gmail address
9. Click **"Save and Continue"**

## Common Error Messages

### "Invalid client" or "Client not found"
- Make sure `credentials.json` is in the same directory as the script
- Verify the file is not corrupted
- Download fresh credentials from Google Cloud Console

### "Access denied" or "Permission denied"
- Ensure you're using the correct Google account
- Check that your email is added as a test user in OAuth consent screen
- Make sure Gmail API is enabled in your project

### "Quota exceeded"
- Gmail API has daily limits
- Wait 24 hours or request quota increase
- Use smaller date ranges for exports

### "Token expired"
- Delete `token.json` file
- Run the script again to re-authenticate

## Alternative Setup Methods

### Method 1: Web Application (if Desktop doesn't work)
1. Create OAuth 2.0 credentials
2. Choose "Web application"
3. Add these redirect URIs:
   - `http://localhost:8080/`
   - `http://localhost:8090/`
   - `http://localhost:9000/`
4. Download and use as `credentials.json`

### Method 2: Service Account (for automation)
1. Create a Service Account
2. Enable domain-wide delegation
3. Download JSON key as `credentials.json`
4. Grant Gmail API permissions

## Quick Test

To test if your setup is working:

```bash
# Run with minimal results first
python gmail_to_csv.py --max-results 10
```

If this works, you can then run larger exports.

## Still Having Issues?

1. **Check your Google Cloud Project**:
   - Ensure Gmail API is enabled
   - Verify OAuth consent screen is configured
   - Check that credentials are for the correct project

2. **Verify file locations**:
   - `credentials.json` should be in the same folder as `gmail_to_csv.py`
   - Check file permissions

3. **Try the setup script**:
   ```bash
   python setup.py
   ```

4. **Check Python version**:
   ```bash
   python --version
   ```
   Should be 3.7 or higher 