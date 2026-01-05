
What this script does:
# Hygraph Blog Import Script

A Python script to batch import blog posts into Hygraph CMS with proper localization support.

## Features

- **Multi-language support**: Groups entries by `blog_post_id` and creates one entry with multiple localizations (de, fr, en, etc.)
- **Rich Text conversion**: Converts HTML content to Hygraph's Slate.js Rich Text format
- **Supports**: Paragraphs, headings (h1-h3), lists (ul, ol), links, bold, italic
- **SEO fields**: Imports all SEO metadata (title, description, keywords, OpenGraph)
- **Dry run mode**: Test the import without creating entries

## Requirements

```bash
pip install pandas requests beautifulsoup4 openpyxl
```

## Setup

### 1. Configure Hygraph

1. Create a **Permanent Auth Token** in your Hygraph project:
   - Go to **Project Settings → API Access → Permanent Auth Tokens**
   - Create a token with **Create** and **Update** permissions for the Blog model

2. Get your **Content API endpoint**:
   - Go to **Project Settings → API Access → Content API**
   - Copy the endpoint URL

### 2. Configure the Script

Edit `hygraph_blog_import.py` and update:

```python
HYGRAPH_ENDPOINT = "https://api-eu-central-1.hygraph.com/v2/YOUR_PROJECT/master"
HYGRAPH_TOKEN = "your-permanent-auth-token"
INPUT_FILE = "sample_blog_import.csv"  # or your CSV/Excel file
```

### 3. Prepare Your Data

Your CSV/Excel file should have these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `blog_post_id` | ✅ | Unique ID for the blog post (same ID = same entry, different locales) |
| `lang_id` | ✅ | Language code (e.g., "de", "fr", "en") |
| `title` | ✅ | Blog post title |
| `short_description` | | Short description/excerpt |
| `content` | | HTML content (will be converted to Rich Text) |
| `search_index` | | Search index text |
| `seo_title` | | SEO title |
| `seo_description` | | SEO description |
| `seo_keywords` | | SEO keywords |
| `og_title` | | OpenGraph title |
| `og_description` | | OpenGraph description |
| `remote_id` | | Remote/legacy ID |
| `remote_slug` | | Remote/legacy slug |

See `sample_blog_import.csv` for an example.

## Usage

### Dry Run (Test Mode)

First, test without creating entries:

```python
DRY_RUN = True
```

```bash
python hygraph_blog_import.py
```

### Full Import

```python
DRY_RUN = False
```

```bash
python hygraph_blog_import.py
```

### Batch Size

To import only the first N blog posts:

```python
BATCH_SIZE = 10  # Only import first 10 unique blog_post_ids
```

Set to `None` to import all.

## Sample Data Structure

The sample CSV contains 5 blog posts with German (de) and French (fr) localizations:

| blog_post_id | Languages | Title |
|--------------|-----------|-------|
| 1 | de, fr | Welcome / Bienvenue |
| 2 | de, fr | Productivity Tips |
| 3 | de, fr | AI Future |
| 4 | fr only | GraphQL Guide |
| 5 | de only | Headless CMS |

## Hygraph Blog Model

Your Hygraph Blog model should have these fields:

- `blogPostId` (Int) - Unique identifier
- `title` (String, Localized) - Blog title
- `shortDescription` (String, Localized) - Short description
- `content` (Rich Text, Localized) - Main content
- `searchIndex` (String, Localized) - Search index
- `seoTitle` (String, Localized) - SEO title
- `seoDescription` (String, Localized) - SEO description
- `seoKeywords` (String, Localized) - SEO keywords
- `ogTitle` (String, Localized) - OpenGraph title
- `ogDescription` (String, Localized) - OpenGraph description
- `remoteId` (Int, Localized) - Legacy ID
- `remoteSlug` (String, Localized, Unique) - Legacy slug

## Supported HTML in Content

The script converts these HTML elements to Slate.js Rich Text:

- `<p>` → Paragraph
- `<h1>`, `<h2>`, `<h3>` → Headings
- `<ul>`, `<ol>`, `<li>` → Lists
- `<a href="...">` → Links
- `<strong>`, `<b>` → Bold
- `<em>`, `<i>` → Italic

## Troubleshooting

### "Input value does not match the expected format"

- Check that your `remoteSlug` values don't contain `/` characters
- Verify Rich Text content structure

### Rate Limiting

Increase `API_DELAY` if you hit rate limits:

```python
API_DELAY = 1.0  # 1 second between requests
```

### Locale Not Found

Make sure the locales (de, fr, etc.) are configured in your Hygraph project:
- **Project Settings → Locales**

## License

MIT

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

