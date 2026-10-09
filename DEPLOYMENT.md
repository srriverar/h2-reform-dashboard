# Deploy H₂ Reform Lab with GitHub and Streamlit Community Cloud

This guide assumes the repository contains `app.py` at its root, as in this package.

## 1. Test locally

Install Python 3.11 or 3.12, then run:

```bash
python -m venv .venv
```

Activate the environment:

```bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install and start the app:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. Stop the server with `Ctrl+C`.

Optional test suite:

```bash
pip install pytest
pytest -q
```

## 2. Create a GitHub repository

1. Sign in at <https://github.com>.
2. Select **New repository**.
3. Use a name such as `h2-reform-dashboard`.
4. Choose **Public** or **Private**. Streamlit Community Cloud must have access to a private repository before it can deploy it.
5. Do not add a README, `.gitignore`, or license if you plan to push this package as-is.
6. Select **Create repository**.

## 3A. Push with Git (recommended)

Extract the ZIP, open a terminal in the extracted folder, and run:

```bash
git init
git add .
git commit -m "Initial H2 Reform Lab dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/h2-reform-dashboard.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If GitHub asks for authentication, use a personal access token or GitHub Desktop; account passwords are not accepted for Git HTTPS operations.

## 3B. Upload using the GitHub website

If you do not want to use Git:

1. Open the empty GitHub repository.
2. Select **uploading an existing file**.
3. Extract this ZIP first.
4. Drag all extracted files and folders into GitHub. Include hidden folders such as `.streamlit` and `.github`.
5. Enter a commit message and select **Commit changes**.

Do not upload the ZIP itself as the only repository file. Streamlit needs the extracted `app.py`, `requirements.txt`, `core/`, and `data/` files.

## 4. Deploy on Streamlit Community Cloud

1. Sign in at <https://share.streamlit.io> using GitHub.
2. Select **Create app** or **New app**.
3. Choose **Deploy a public app from GitHub** (wording may vary).
4. Select:
   - **Repository:** `YOUR_USERNAME/h2-reform-dashboard`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. In advanced settings, select Python 3.11 or 3.12 if the option is shown.
6. No secrets are required for this version.
7. Select **Deploy**.

Streamlit will install `requirements.txt`, start `app.py`, and provide a public URL similar to:

```text
https://h2-reform-dashboard.streamlit.app
```

The first deployment can take several minutes while SciPy and the other dependencies are installed.

## 5. Update the deployed dashboard

Edit the project locally, test it, then push the changes:

```bash
git add .
git commit -m "Describe the dashboard update"
git push
```

Streamlit Community Cloud normally detects the new commit and redeploys automatically.

## 6. Troubleshooting

### `ModuleNotFoundError`

Confirm the missing package is listed in `requirements.txt`. Internal imports require the `core/` folder and `core/__init__.py` to remain in the repository.

### `FileNotFoundError` for the literature matrix

Confirm these repository paths exist exactly as written:

```text
data/literature_matrix.csv
data/demo_experimental.csv
```

Linux paths are case-sensitive.

### The app cannot find `app.py`

Set the Streamlit main file path to `app.py`. If you placed all files inside an extra folder in the repository, use `folder_name/app.py` instead.

### Deployment fails while installing dependencies

Use Python 3.11 or 3.12 in Streamlit advanced settings, reboot the app, and review the deployment log. The supplied dependency ranges support those versions.

### A private GitHub repository is not listed

Authorize Streamlit Community Cloud to access that repository in GitHub, then refresh the repository selector.

## Repository checklist

Before deploying, verify that GitHub shows:

```text
.github/workflows/tests.yml
.streamlit/config.toml
app.py
core/__init__.py
core/metrics.py
core/thermodynamics.py
data/demo_experimental.csv
data/literature_matrix.csv
tests/test_thermodynamics.py
requirements.txt
README.md
DEPLOYMENT.md
```

Never commit `.streamlit/secrets.toml`, API keys, passwords, experimental data covered by an NDA, `.venv`, or local cache files.
