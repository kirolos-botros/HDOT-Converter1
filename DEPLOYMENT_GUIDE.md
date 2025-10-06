# Deployment Guide for HeadLight to ODOT Converter

## Step-by-Step Instructions for GitHub + Streamlit Deployment

### Step 1: Create GitHub Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" button in the top right corner
3. Select "New repository"
4. Fill in:
   - Repository name: `headlight-odot-converter`
   - Description: "HeadLight to ODOT PDF Converter - Web Application"
   - Make it **Public** (required for free Streamlit hosting)
   - Don't initialize with README, .gitignore, or license
5. Click "Create repository"

### Step 2: Upload Files to GitHub
1. Download the files from this folder:
   - `main.py`
   - `streamlit_app.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
   - `.streamlit/config.toml`
   - `ODOT Template.pdf`

2. In your GitHub repository:
   - Click "uploading an existing file"
   - Drag and drop all the files above
   - Add a commit message: "Initial commit - HeadLight to ODOT converter"
   - Click "Commit changes"

### Step 3: Deploy to Streamlit
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Fill in:
   - Repository: `yourusername/headlight-odot-converter`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
5. Click "Deploy!"

### Step 4: Share with Customers
1. Once deployed, you'll get a URL like: `https://headlight-odot-converter-yourusername.streamlit.app`
2. Share this URL with your customers
3. They can use it directly in their browser - no downloads needed!

## Files Included
- `main.py` - Core conversion logic
- `streamlit_app.py` - Web interface
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules
- `.streamlit/config.toml` - Streamlit configuration
- `ODOT Template.pdf` - ODOT form template

## Customer Usage
Your customers will:
1. Go to your Streamlit URL
2. Upload their HeadLight JSON file
3. Optionally upload photos
4. Click "Convert to ODOT PDF"
5. Download the generated PDF

No software installation required!
