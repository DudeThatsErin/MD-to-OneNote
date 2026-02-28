# Markdown (md) to OneNote

This tool lets you bulk import your Obsidian vault or UpNote backup into Microsoft OneNote. It keeps your folder structure intact by converting folders into sections and section groups, and uses the file name as the note title.

## Features

- Folder structure preserved - nested folders become section groups and sections
- File name becomes note title - no metadata needed
- Markdown rendered - headings, bold/italic, code blocks, tables, blockquotes, links, and images all convert
- Obsidian-aware - strips YAML front matter, converts [[wiki links]], and handles callouts (> [!NOTE])
- Local images inlined - relative image references get embedded as base64 so they show up in OneNote
- Skip duplicates - notes that already exist in OneNote are skipped by default
- Dry run mode - preview what will be imported without actually touching OneNote
- Rate-limit safe - configurable delay between API calls so you don't get throttled
- Free to use - the Microsoft Graph API for OneNote is free, you just need a Microsoft account
- Cross-platform - works on Windows, macOS, and Linux

## Platform Support

| Platform | Status | Notes |
|---|---|---|
| Windows 10/11 | Fully supported | Use `run.bat` for one-click launch |
| macOS | Fully supported | Use `run.sh` for one-click launch |
| Linux | Fully supported | Use `run.sh` for one-click launch |

## Folder -> OneNote Structure

```
vault/                          -> Notebook (you name it)
vault/note.md                   -> Page in section "_Root Notes"
vault/FolderA/note.md           -> Page in section "FolderA"
vault/FolderA/SubB/note.md      -> Section Group "FolderA" -> Section "SubB" -> Page
vault/A/B/C/note.md             -> SectionGroup "A" -> SectionGroup "B" -> Section "C" -> Page
```

> OneNote limitation: Section groups can only be nested up to 3 levels deep via the API. If your vault is deeper than that the tool will still work, it just creates sections at the deepest allowed level.

---

## Quick Start (One-Click)

If you don't want to mess with the command line:

- Windows: Double-click `run.bat` and it will ask you for your vault path and notebook name
- Mac/Linux: Run `./run.sh` in a terminal and it will do the same

Both scripts install dependencies automatically on first run. You still need to do the Azure App setup and create a `.env` file first (see [Setup](#setup) below).

You can also pass the paths directly to skip the prompts:
```bash
# Windows
run.bat "D:\Obsidian\My Vault" "Imported Notes"

# Mac/Linux
./run.sh "/Users/yourname/Obsidian/My Vault" "Imported Notes"
```

---

## Setup

### 1. Install Python

**Windows:**
- Download from [https://www.python.org/downloads/](https://www.python.org/downloads/)
- During install, make sure to check "Add Python to PATH"
- To verify it worked, open PowerShell and run `python --version`

**macOS:**
```bash
brew install python
# or just download it from https://www.python.org/downloads/
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3 python3-pip
```

### 2. Install dependencies

**Windows (PowerShell):**
```powershell
python -m pip install -r requirements.txt
```

**Mac/Linux:**
```bash
pip3 install -r requirements.txt
```

### 3. Register an Azure App (one-time, ~5 minutes)

You need a free Azure App Registration to get a Client ID for the Microsoft Graph API. This is NOT an App Service or Web App, it's just a free identity registration.

1. Go to [https://portal.azure.com](https://portal.azure.com) and sign in with the Microsoft account that has your OneNote
2. In the top search bar, search for "App registrations" and click it under Services

   Do NOT click "App Services" - that's for hosting websites and is not what you want here.

3. Click + New registration
4. Fill in:
   - Name: `md-to-onenote` (or anything you want)
   - Supported account types: select "Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts"

   Do NOT select "My organization only" - that will block your personal Microsoft account from logging in.

   - Redirect URI: leave this blank
5. Click Register
6. On the overview page, copy the Application (client) ID - you'll need it in step 4

7. In the left sidebar, click Authentication (not "Authentication (Preview)")
   - Scroll down to Advanced settings
   - Set "Allow public client flows" to Yes
   - Click Save at the top

   This step is required. If you skip it you will get this error: `AADSTS70002: The provided client is not supported for this feature. The client application must be marked as 'mobile.'`

8. In the left sidebar, click API permissions
   - Click Add a permission -> Microsoft Graph -> Delegated permissions
   - Search for and add each of these:
     - `Notes.ReadWrite`
     - `Notes.Create`
     - `Notes.ReadWrite.All`
   - Click Add permissions

### 4. Configure

**Windows:** Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

Then open `.env` and paste in your Client ID from step 3:
```
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Usage

### Do a dry run first (recommended)

This lets you preview what will be imported without actually touching OneNote:

**Windows:**
```powershell
python main.py import --vault "D:\Obsidian\My Vault" --notebook "Imported Notes" --dry-run
```

**Mac/Linux:**
```bash
python3 main.py import --vault "/Users/yourname/Obsidian/My Vault" --notebook "Imported Notes" --dry-run
```

> Windows tip: If your vault path has an apostrophe in it (like `Erin's Vault`), check the actual folder name on disk first. Windows sometimes strips apostrophes from folder names on certain drives. Run this to see the real name:
> ```powershell
> Get-ChildItem D:\ | Select-Object Name
> ```

### Import your vault
**Windows:**
```powershell
python main.py import --vault "D:\Obsidian\My Vault" --notebook "Imported Notes"
```

**Mac/Linux:**
```bash
python3 main.py import --vault "/Users/yourname/Obsidian/My Vault" --notebook "Imported Notes"
```

The first time you run this, you'll see something like:

```
To sign in, use a web browser to open https://microsoft.com/devicelogin
and enter the code XXXXXXXX to authenticate.
```

Open that URL, enter the code, and sign in with your Microsoft account. Your token gets cached locally so you only have to do this once.

The `--notebook` flag is the name of the OneNote notebook you want to import into. If it doesn't exist yet it gets created automatically. I recommend using a fresh notebook name so you can organize everything later.

### Importing an UpNote backup

UpNote exports as a folder per notebook. Just point `--vault` at the root export folder:

**Windows:**
```powershell
python main.py import --vault "D:\UpNote Export" --notebook "Imported from UpNote"
```

**Mac/Linux:**
```bash
python3 main.py import --vault "~/UpNote Export" --notebook "Imported from UpNote"
```

### All options

```
--vault PATH             Path to your vault/backup folder  [required]
--notebook TEXT          Target OneNote notebook name      [required]
--client-id TEXT         Azure App Client ID (or set AZURE_CLIENT_ID in .env)
--skip-existing          Skip notes already in OneNote     [default: on]
--overwrite              Re-import notes even if they already exist
--ignore-templates       Skip folders named "templates"    [default: on]
--include-templates      Import template folders too
--delay INTEGER          Milliseconds between API calls    [default: 1000]
--dry-run                Preview only, no changes made
```

### Other useful commands

**Windows:**
```powershell
# See all your OneNote notebooks
python main.py list-notebooks

# Test that auth is working
python main.py auth

# Sign out and clear the cached token
python main.py auth --logout
```

**Mac/Linux:**
```bash
python3 main.py list-notebooks
python3 main.py auth
python3 main.py auth --logout
```

---

## Building a Standalone EXE

If you want to give this to someone who doesn't have Python installed, you can build a single executable with PyInstaller.

**Windows:**
```powershell
pip install pyinstaller
pyinstaller --onefile --name md-to-onenote main.py
```

The output will be at `dist\md-to-onenote.exe`. Whoever uses it still needs to:
1. Put a `.env` file with their `AZURE_CLIENT_ID` in the same folder as the `.exe`
2. Do the Azure App Registration steps above first

> Note: The `.exe` will be around 20-40 MB since PyInstaller bundles the Python runtime with it. Windows Defender might flag it as unknown on first run. Just click "More info" then "Run anyway" - this is normal for unsigned apps.

**Mac:**
```bash
pip3 install pyinstaller
pyinstaller --onefile --name md-to-onenote main.py
```

Output goes to `dist/md-to-onenote`. Make it executable first:
```bash
chmod +x dist/md-to-onenote
```

> Note: macOS will block unsigned apps by default. Right-click it, click Open, then click Open anyway. Or run this in Terminal: `xattr -d com.apple.quarantine dist/md-to-onenote`

---

## Supported Markdown Features

| Feature | Converted to |
|---|---|
| `# H1` through `###### H6` | OneNote headings |
| `**bold**`, `*italic*` | Bold, italic |
| `` `inline code` `` | Styled inline code |
| ` ```code blocks``` ` | Styled pre/code blocks |
| `> blockquotes` | Indented blockquote style |
| `- [ ]` / `- [x]` task lists | text |
| `\| table \|` | Styled HTML table |
| `[link](url)` | Hyperlink |
| `![img](path)` | Inlined image (local) or external img tag |
| `---` | Horizontal rule |
| YAML front matter | Stripped (not imported) |
| `[[wiki links]]` | Converted to plain text |
| Obsidian callouts `> [!NOTE]` | Styled blockquote |

---

## Known Limitations

- Rate limits: The Graph API allows roughly 4 requests/second. The default `--delay 1000` is safe for most vaults but if you still hit throttle errors try bumping it to `--delay 2000` or higher. If you have a smaller vault and want it to go faster, `--delay 500` usually works fine.
- Section group nesting: OneNote only allows 3 levels of nesting via the API. Very deep folder structures get flattened at level 3.
- Images: Only local images with relative paths get inlined. External image URLs are passed through as-is.
- File attachments: Non-image attachments like PDFs are not uploaded. Their links will just show as text.
- Large vaults: If you have 1000+ notes expect the import to take 10-20+ minutes because of API rate limits.
- Token cache: Saved to `.token_cache.json` in the project folder. Delete it or run `python main.py auth --logout` to sign out.

---

## FAQ

#### **Is this free?**

Yes. The Microsoft Graph API for OneNote is free with any Microsoft account. The Azure App Registration is also free. If you have a Pay As You Go Azure subscription you won't be charged anything for this - there's no compute or storage involved on Azure's side.

#### **I get `AADSTS70002: The provided client is not supported for this feature. The client application must be marked as 'mobile.'`**

You need to enable public client flows. Go to your app registration in the Azure Portal -> Authentication (in the left sidebar, not "Authentication (Preview)") -> scroll to Advanced settings -> set "Allow public client flows" to Yes -> click Save.

#### **Authentication fails and it says "My organization only"**

The app was registered with the wrong account type. Go to your app registration -> Authentication -> change Supported account types to "Accounts in any organizational directory... and personal Microsoft accounts" -> Save.

#### **My vault path has an apostrophe and it says the folder doesn't exist**

Windows sometimes strips apostrophes from folder names on certain drives. Run `Get-ChildItem <drive>:\` in PowerShell to see the actual folder name and use that in `--vault`.

#### **How does it know which notebook to import into?**

You tell it with `--notebook "My Notebook Name"`. If that notebook already exists it imports into it, if not it creates it. Use a new name if you want a clean notebook to organize later.

#### **Can I re-run it without creating duplicates?**

Yes. `--skip-existing` is on by default and checks if a page with the same title already exists in the same section before creating it. Use `--overwrite` if you want to force everything to re-import.

#### **What if I only want to import part of my vault?**
Just point `--vault` at a subfolder instead of the vault root and only notes in that folder will get imported.

#### **Why does the progress bar look garbled with overlapping percentages in PowerShell?**
That's just PowerShell not handling the terminal control codes that the progress bar uses to update in place. It's still working fine - those are just partial renders of the same progress line updating as notes get imported. It'll look clean if you run it from Windows Terminal instead of plain PowerShell, but it's purely cosmetic and doesn't affect anything.
