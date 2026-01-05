#!/usr/bin/env python3
"""
Hygraph Blog Batch Import Script
Reads from Excel file and creates blog entries with proper localization via Content API
"""

import pandas as pd
import requests
import json
import re
import time
from bs4 import BeautifulSoup
from html import unescape

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# =============================================================================
HYGRAPH_ENDPOINT = "https://eu-west-2-ssc.cdn.hygraph.com/content/cmiwy6t0d001k06w4oqvmieqy/master"  # e.g., https://api-eu-central-1.hygraph.com/v2/xxx/master
HYGRAPH_TOKEN = "eyJ2ZXJzaW9uIjozLCJpYXQiOjE3NjUxODYwOTAsImF1ZCI6WyJodHRwczovL2FwaS1ldS13ZXN0LTItc3NjLmh5Z3JhcGguY29tL3YyL2NtaXd5NnQwZDAwMWswNnc0b3F2bWllcXkvbWFzdGVyIiwibWFuYWdlbWVudC1uZXh0LmdyYXBoY21zLmNvbSJdLCJpc3MiOiJodHRwczovL21hbmFnZW1lbnQtZXUtd2VzdC0yLXNzYy5oeWdyYXBoLmNvbS8iLCJzdWIiOiJiMDA4OTJmZi03MmZkLTQ3NDYtOWU0Yi0xYjljNTRjNTdmMGQiLCJqdGkiOiJjbWl3eTgwODUwMDZoMDdtbTNodHo3enR6In0.ehkUF-O13cEb4pSGmA7I1mRqQlcrAgG_f3IpPTYOZfM82qvecTKJ2YDFIlfvgZnhr23QHcwK8lTYBSniYPf3v6bNDamB7STPoHfTdWdmqG3-53iv2D4-d7XZwIlOJUkLoha5vV_9Yb58lMNpg_rmUkJzbO4SlMgOS--2TGA79D9VtYw9zqA2XwItNpYefpyqVnwjpAtB9K7Wk02b8QErGhQyvoDVV0EChC0i7lVAZOQNk8hP3spxOCxMLC_4HY6j6VPL5zGUPS-AIN6zVr2gS-kJaEDL0BtnjkFUsfUfUnniv3UtW8JQlq1WYBSUCJgSN0eYhLpYlCW4jhoYs_yi5LT08rPOvavLglGP1LIaTOcyS7UMMLJerkZ7hA51-HG1r9r0JK3lg8R6PQfOABCHUm-NrGMeXqSN0MBPgfcztY508g7qjF2nbWbA4Rxmg0GQiEXK-s3apeLIYYvx3HFMt-dUgWUVdSj6I-Nu_YD3Rkk-LEFXCEXR_LItKjZUyGA4eeFROb6m9SMrNeejeGqgbcq_GTw7SbddTNShGq44a5oEfr3fPKUB7_0Ia8BcYbToHCN52rkrdbXJMyo7_UgUaA1pLye4cUuxkT0RyPQ6G0P9MIAi2ZTJz4GzPE4gagtjsRqwh9cWAj1FrPEA2kmT2GUYmnOqpqJF1ZmLTMpkqH0"  # Create in Project Settings > API Access > Permanent Auth Tokens
EXCEL_FILE = "sample_blog_import.xlsx"
BATCH_SIZE = 3  # Number of unique blog_post_ids to import (set to None for all)
# Dry run mode - set to True to test without creating entries
DRY_RUN = True
# =============================================================================


def html_to_slate(html_content):
    """Convert HTML to Slate.js AST format for Hygraph Rich Text"""
    if pd.isna(html_content) or not html_content:
        return None
    
    content = str(html_content)
    # Clean up XML/HTML
    content = re.sub(r'<row[^>]*>', '', content)
    content = re.sub(r'</row>', '', content)
    content = re.sub(r'<column[^>]*>', '', content)
    content = re.sub(r'</column>', '', content)
    content = re.sub(r'<column_text>', '', content)
    content = re.sub(r'</column_text>', '', content)
    content = re.sub(r'<column_image[^>]*/?>', '', content)
    content = re.sub(r'</column_image>', '', content)
    content = re.sub(r'<column_blog_products[^>]*/?>', '', content)
    content = re.sub(r'<!\[CDATA\[', '', content)
    content = re.sub(r'\]\]>', '', content)
    content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL)
    
    soup = BeautifulSoup(content, 'html.parser')
    children = []
    
    def process_inline(element):
        result = []
        if isinstance(element, str):
            text = element.strip()
            if text:
                result.append({"text": unescape(text)})
        elif element.name == 'a':
            href = element.get('href', '')
            link_text = element.get_text().strip()
            if link_text and href:
                result.append({"type": "link", "href": href, "children": [{"text": link_text}]})
            elif link_text:
                result.append({"text": link_text})
        elif element.name in ['strong', 'b']:
            text = element.get_text().strip()
            if text:
                result.append({"text": text, "bold": True})
        elif element.name in ['em', 'i']:
            text = element.get_text().strip()
            if text:
                result.append({"text": text, "italic": True})
        elif hasattr(element, 'children'):
            for child in element.children:
                result.extend(process_inline(child))
        return result
    
    def process_element(element):
        if isinstance(element, str):
            text = element.strip()
            if text and text != '\n':
                return [{"type": "paragraph", "children": [{"text": unescape(text)}]}]
            return []
        
        if element.name == 'p':
            inline_children = []
            for child in element.children:
                inline_children.extend(process_inline(child))
            if not inline_children:
                return []
            return [{"type": "paragraph", "children": inline_children}]
        elif element.name == 'h1':
            text = element.get_text().strip()
            return [{"type": "heading-one", "children": [{"text": text}]}] if text else []
        elif element.name == 'h2':
            text = element.get_text().strip()
            return [{"type": "heading-two", "children": [{"text": text}]}] if text else []
        elif element.name == 'h3':
            text = element.get_text().strip()
            return [{"type": "heading-three", "children": [{"text": text}]}] if text else []
        elif element.name in ['ul', 'ol']:
            list_type = "bulleted-list" if element.name == 'ul' else "numbered-list"
            items = []
            for li in element.find_all('li', recursive=False):
                li_text = li.get_text().strip()
                if li_text:
                    items.append({
                        "type": "list-item",
                        "children": [{"type": "list-item-child", "children": [{"type": "paragraph", "children": [{"text": li_text}]}]}]
                    })
            return [{"type": list_type, "children": items}] if items else []
        elif element.name == 'table':
            rows = []
            for tr in element.find_all('tr'):
                cells = [td.get_text().strip() for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(" | ".join(cells))
            return [{"type": "paragraph", "children": [{"text": "\n".join(rows)}]}] if rows else []
        elif element.name == 'div' or hasattr(element, 'children'):
            results = []
            for child in element.children:
                results.extend(process_element(child))
            return results
        return []
    
    for element in soup.children:
        children.extend(process_element(element))
    
    # Filter empty paragraphs
    children = [c for c in children if c.get('children') and any(
        child.get('text', '').strip() or child.get('type') == 'link' 
        for child in c.get('children', [])
    )]
    
    return {"children": children} if children else None


def sanitize_slug(slug):
    if pd.isna(slug) or not slug:
        return None
    return str(slug).replace('/', '-').strip('-')


def create_blog_entry(endpoint, token, data, dry_run=False):
    """Create a blog entry via Hygraph Content API"""
    if dry_run:
        return {"data": {"createBlog": {"id": "dry-run-id", "blogPostId": data.get("blogPostId")}}}
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    mutation = """
    mutation CreateBlog($data: BlogCreateInput!) {
      createBlog(data: $data) {
        id
        blogPostId
        title
        localizations {
          locale
          title
        }
      }
    }
    """
    
    payload = {
        "query": mutation,
        "variables": {"data": data}
    }
    
    response = requests.post(endpoint, headers=headers, json=payload)
    return response.json()


def main():
    print("=" * 70)
    print("HYGRAPH BLOG BATCH IMPORT")
    print("=" * 70)
    
    # Validate configuration
    if HYGRAPH_ENDPOINT == "YOUR_HYGRAPH_CONTENT_API_ENDPOINT":
        print("\n❌ ERROR: Please update HYGRAPH_ENDPOINT in the script")
        print("   Find it in: Project Settings > API Access > Content API")
        return
    
    if HYGRAPH_TOKEN == "YOUR_PERMANENT_AUTH_TOKEN":
        print("\n❌ ERROR: Please update HYGRAPH_TOKEN in the script")
        print("   Create it in: Project Settings > API Access > Permanent Auth Tokens")
        print("   Make sure it has 'Create' and 'Update' permissions for Blog model")
        return
    
    if DRY_RUN:
        print("\n⚠️  DRY RUN MODE - No entries will be created")

        
    # Read Excel file
    print(f"\n📖 Reading {EXCEL_FILE}...")
    try:
        df = pd.read_excel(EXCEL_FILE)
        print(f"   Found {len(df)} rows")
    except FileNotFoundError:
        print(f"\n❌ ERROR: File not found: {EXCEL_FILE}")
        return
    
    # Group by blog_post_id
    print("\n🔄 Grouping entries by blog_post_id...")
    blog_groups = {}
    for i, row in df.iterrows():
        bid = int(row['blog_post_id'])
        lang = row['lang_id']
        
        if bid not in blog_groups:
            blog_groups[bid] = {}
        
        blog_groups[bid][lang] = {
            'title': row['title'] if pd.notna(row['title']) else None,
            'shortDescription': row['short_description'][:500] if pd.notna(row['short_description']) else None,
            'content': html_to_slate(row['content']),
            'remoteId': int(row['remote_id']) if pd.notna(row['remote_id']) else None,
            'remoteSlug': row['remote_slug'],
        }
    
    print(f"   Found {len(blog_groups)} unique blog entries")
    
    # Limit to batch size
    blog_ids = list(blog_groups.keys())
    if BATCH_SIZE:
        blog_ids = blog_ids[:BATCH_SIZE]
    
    print(f"\n📝 Will import {len(blog_ids)} entries")
    
    # Import each entry
    success_count = 0
    error_count = 0
    
    for bid in blog_ids:
        langs = blog_groups[bid]
        
        # Determine primary locale (prefer 'de' if available)
        if 'de' in langs:
            primary_locale = 'de'
        elif 'fr' in langs:
            primary_locale = 'fr'
        else:
            primary_locale = list(langs.keys())[0]
        
        primary_data = langs[primary_locale]
        other_locales = {k: v for k, v in langs.items() if k != primary_locale}
        
        print(f"\n   Creating blog_post_id={bid} (primary: {primary_locale}, localizations: {list(other_locales.keys())})")
        
        # Build mutation data
        mutation_data = {
            "blogPostId": bid,
            "title": primary_data['title'],
        }
        
        if primary_data['shortDescription']:
            mutation_data["shortDescription"] = primary_data['shortDescription']
        if primary_data['remoteId']:
            mutation_data["remoteId"] = primary_data['remoteId']
        if primary_data['remoteSlug']:
            mutation_data["remoteSlug"] = primary_data['remoteSlug']
        if primary_data['content']:
            mutation_data["content"] = primary_data['content']
        
        # Add localizations
        if other_locales:
            loc_creates = []
            for locale, loc_data in other_locales.items():
                loc_entry = {
                    "locale": locale,
                    "data": {
                        "title": loc_data['title']
                    }
                }
                if loc_data['shortDescription']:
                    loc_entry["data"]["shortDescription"] = loc_data['shortDescription']
                if loc_data['remoteId']:
                    loc_entry["data"]["remoteId"] = loc_data['remoteId']
                if loc_data['remoteSlug']:
                    loc_entry["data"]["remoteSlug"] = loc_data['remoteSlug']
                if loc_data['content']:
                    loc_entry["data"]["content"] = loc_data['content']
                loc_creates.append(loc_entry)
            mutation_data["localizations"] = {"create": loc_creates}
        
        # Execute mutation
        result = create_blog_entry(HYGRAPH_ENDPOINT, HYGRAPH_TOKEN, mutation_data, DRY_RUN)
        
        if "errors" in result:
            print(f"      ❌ Error: {result['errors'][0]['message']}")
            error_count += 1
        else:
            entry_id = result.get('data', {}).get('createBlog', {}).get('id', 'unknown')
            print(f"      ✅ Created: {entry_id}")
            success_count += 1
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors:  {error_count}")
    print(f"   Total:     {success_count + error_count}")


if __name__ == "__main__":
    main()
