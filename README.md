# md-to-onenote

Bulk import Obsidian vaults and UpNote backups into Microsoft OneNote, preserving your folder structure as OneNote sections and section groups.

## Features

- **Folder structure preserved** — nested folders become section groups and sections
- **File name becomes note title** — no metadata needed
- **Markdown rendered** — headings, bold/italic, code blocks, tables, blockquotes, links, images all convert
- **Obsidian-aware** — strips YAML front matter, converts `[[wiki links]]`, handles callouts (`> [!NOTE]`)
- **Local images inlined** — relative image references are embedded as base64 so they appear in OneNote
- **Skip duplicates** — already-imported notes are skipped by default
- **Dry run mode** — preview what will be imported without touching OneNote
- **Rate-limit safe** — configurable delay between API calls
- **Free to use** — the Microsoft Graph API for OneNote has no per-call cost; you only need a Microsoft account
- **Cross-platform** — works on Windows, macOS, and Linux

## Platform Support

| Platform | Status | Notes |
|---|---|---|
| Windows 10/11 | ✅ Fully supported | Use `run.bat` for one-click launch |
| macOS | ✅ Fully supported | Use `run.sh` for one-click launch |
| Linux | ✅ Fully supported | Use `run.sh` for one-click launch |

## Folder → OneNote Structure

```
vault/                          → Notebook (you name it)
vault/note.md                   → Page in section "_Root Notes"
vault/FolderA/note.md           → Page in section "FolderA"
vault/FolderA/SubB/note.md      → Section Group "FolderA" → Section "SubB" → Page
vault/A/B/C/note.md             → SectionGroup "A" → SectionGroup "B" → Section "C" → Page
```

> **OneNote limitation:** Section groups can be nested up to 3 levels deep via the API. If your vault is deeper than that, the tool will still work — it creates sections at the deepest allowed level.

---

## Quick Start (One-Click)

If you just want to run it without typing commands:

- **Windows:** Double-click `run.bat` — it will prompt you for your vault path and notebook name
- **Mac/Linux:** Run `./run.sh` in a terminal — same prompts

Both scripts automatically install dependencies on first run. You still need to complete the Azure App setup and create a `.env` file first (see [Setup](#setup) below).

You can also pass arguments directly to skip the prompts:
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
- During install, check **"Add Python to PATH"**
- Verify: open PowerShell and run `python --version`

**macOS:**
```bash
brew install python
# or download from https://www.python.org/downloads/
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

You need a free Azure App Registration to get a Client ID for the Microsoft Graph API. This is **not** an App Service or Web App — it's just an identity registration that costs nothing.

1. Go to [https://portal.azure.com](https://portal.azure.com) and sign in with your **Microsoft account** (the same account that has OneNote)
2. In the top search bar, search for **"App registrations"** and click it under **Services**

   > ⚠️ Do **not** click "App Services" — that is for hosting websites and is not what you want.

3. Click **+ New registration**
4. Fill in:
   - **Name:** `md-to-onenote` (anything you like)
   - **Supported account types:** select **"Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant) and personal Microsoft accounts"**

   > ⚠️ Do **not** select "My organization only" — that will block your personal Microsoft account from authenticating.

   - **Redirect URI:** leave blank
5. Click **Register**
6. On the overview page, copy the **Application (client) ID** — you'll need it shortly

7. In the left sidebar, click **Authentication** (not "Authentication (Preview)")
   - Scroll down to **Advanced settings**
   - Set **"Allow public client flows"** to **Yes**
   - Click **Save** at the top

   > ⚠️ This step is required. If you skip it you will get the error: `AADSTS70002: The provided client is not supported for this feature. The client application must be marked as 'mobile.'`

8. In the left sidebar, click **API permissions**
   - Click **Add a permission** → **Microsoft Graph** → **Delegated permissions**
   - Search for and add each of these:
     - `Notes.ReadWrite`
     - `Notes.Create`
     - `Notes.ReadWrite.All`
   - Click **Add permissions**

### 3. Configure

**Windows:** Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

**Mac/Linux:**
```bash
cp .env.example .env
```

Then open `.env` and paste in your Client ID:
```
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## Usage

### Dry run first (recommended)

Preview what will be imported without touching OneNote:

**Windows:**
```powershell
python main.py import --vault "D:\Obsidian\My Vault" --notebook "Imported Notes" --dry-run
```

**Mac/Linux:**
```bash
python3 main.py import --vault "/Users/yourname/Obsidian/My Vault" --notebook "Imported Notes" --dry-run
```

> **Tip (Windows):** If your vault path contains an apostrophe (e.g. `Erin's Vault`), check the actual folder name on disk — Windows sometimes strips apostrophes when creating folders on certain drives. Use `Get-ChildItem` to confirm the exact name:
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

The first time you run this, output like the following will appear:

```
To sign in, use a web browser to open https://microsoft.com/devicelogin
and enter the code XXXXXXXX to authenticate.
```

Open that URL in your browser, enter the code, and sign in with your Microsoft account. Your token is cached locally so you only need to do this once.

The `--notebook` name is the OneNote notebook to import into. If it doesn't exist it will be created automatically. Use a fresh notebook name if you want a clean slate to organize later.

### UpNote backup

UpNote's export creates a folder per notebook. Point `--vault` at the root export folder:

**Windows:**
```powershell
python main.py import --vault "D:\UpNote Export" --notebook "Imported from UpNote"
```

**Mac/Linux:**
```bash
python3 main.py import --vault "~/UpNote Export" --notebook "Imported from UpNote"
```

### Options

```
--vault PATH             Path to your vault/backup folder  [required]
--notebook TEXT          Target OneNote notebook name      [required]
--client-id TEXT         Azure App Client ID (or set AZURE_CLIENT_ID in .env)
--skip-existing          Skip notes already in OneNote     [default: on]
--overwrite              Re-import notes even if they exist
--ignore-templates       Skip folders named "templates"    [default: on]
--include-templates      Import template folders too
--delay INTEGER          Milliseconds between API calls    [default: 300]
--dry-run                Preview only, no changes made
```

### Other commands

**Windows:**
```powershell
python main.py list-notebooks
python main.py auth
python main.py auth --logout
```

**Mac/Linux:**
```bash
python3 main.py list-notebooks
python3 main.py auth
python3 main.py auth --logout
```

---

## Building a Standalone EXE (Windows)

If you want a single `.exe` file you can hand to someone who doesn't have Python installed:

```powershell
pip install pyinstaller
pyinstaller --onefile --name md-to-onenote main.py
```

The output will be at `dist\md-to-onenote.exe`. The recipient still needs to:
1. Have a `.env` file with their `AZURE_CLIENT_ID` in the same folder as the `.exe`
2. Complete the Azure App Registration steps above

> **Note:** The `.exe` will be 20-40 MB because PyInstaller bundles the Python runtime. Windows Defender may flag it as unknown on first run — click "More info" → "Run anyway" (this is normal for unsigned executables).

### Building a standalone app on Mac

```bash
pip3 install pyinstaller
pyinstaller --onefile --name md-to-onenote main.py
```

Output will be at `dist/md-to-onenote`. Make it executable:
```bash
chmod +x dist/md-to-onenote
```

> **Note:** macOS will block unsigned apps. Right-click → Open → Open anyway on first run, or run `xattr -d com.apple.quarantine dist/md-to-onenote` in Terminal.

---

## Supported Markdown Features

| Feature | Converted to |
|---|---|
| `# H1` through `###### H6` | OneNote headings |
| `**bold**`, `*italic*` | Bold, italic |
| `` `inline code` `` | Styled inline code |
| ` ```code blocks``` ` | Styled pre/code blocks |
| `> blockquotes` | Indented blockquote style |
| `- [ ]` / `- [x]` task lists | ☐ / ✅ text |
| `\| table \|` | Styled HTML table |
| `[link](url)` | Hyperlink |
| `![img](path)` | Inlined image (local) or external img tag |
| `---` | Horizontal rule |
| YAML front matter | Stripped (not imported) |
| `[[wiki links]]` | Converted to plain text |
| Obsidian callouts `> [!NOTE]` | Styled blockquote |

---

## Notes & Limitations

- **OneNote API rate limits:** The API allows roughly 4 requests/second. The default `--delay 300` respects this. If you hit throttle errors, increase to `--delay 500` or higher.
- **Section group nesting:** OneNote's API supports up to 3 levels of section group nesting. Very deep vault structures will be flattened at level 3.
- **Images:** Only local images referenced with relative paths are inlined. External URLs are passed through as-is.
- **Attachments:** Non-image file attachments (PDFs, etc.) are not uploaded — their links will appear as text.
- **Large vaults:** For 1000+ notes, expect the import to take 10-20+ minutes due to API rate limits.
- **Token cache:** Stored in `.token_cache.json` in the project folder. Delete this file or run `python main.py auth --logout` to re-authenticate.

---

## FAQ

**Is this free?**
Yes. The Microsoft Graph API for OneNote is included with any Microsoft account at no cost. The Azure App Registration is also free. If you're on a Pay As You Go Azure subscription, you will not be charged anything for using this tool — no compute or storage is involved on Azure's side.

**I get `AADSTS70002: The provided client is not supported for this feature. The client application must be marked as 'mobile.'`**
You forgot to enable public client flows. In the Azure Portal, go to your app registration → **Authentication** (in the left sidebar, not "Authentication (Preview)") → scroll to **Advanced settings** → set **Allow public client flows** to **Yes** → click **Save**.

**I get `Supported account types: My organization only` and authentication fails**
The app was registered with the wrong account type. Go to your app registration → **Authentication** → under **Supported account types**, change to **"Accounts in any organizational directory... and personal Microsoft accounts"** → Save.

**My vault path has an apostrophe and the tool says the directory doesn't exist**
Windows sometimes silently strips apostrophes from folder names on certain drives/filesystems. Run `Get-ChildItem <drive>:\` in PowerShell to see the actual folder name on disk and use that exact name in `--vault`.

**How does it know which notebook to import into?**
You specify it with `--notebook "My Notebook Name"`. If a notebook with that name already exists in your OneNote account it will import into it; if not, it creates a new one. Use a fresh name if you want a clean notebook to organize later.

**Can I re-run it without creating duplicates?**
Yes. By default `--skip-existing` is on, which checks for a page with the same title in the same section before creating it. Run with `--overwrite` if you want to force re-import everything.

**What if I only want to import part of my vault?**
Point `--vault` at any subfolder rather than the vault root. Only notes inside that folder will be imported.
