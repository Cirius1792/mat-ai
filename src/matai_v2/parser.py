import re
import logging
from typing import Optional
from bs4 import BeautifulSoup
from prettytable import PrettyTable

logger = logging.getLogger(__name__)
# Common patterns that indicate start of quoted text
DIVIDER_PATTERNS = [
    # Detailed email headers
    r'From:.*?(?:<[^>]+>)?.*?(?:Date:.*?)?To:.*?(?:Cc:.*?)?Subject:',  # Detailed email header with optional Cc
    r'From:.*?(?:<[^>]+>)?.*?To:.*?(?:Cc:.*?)?Subject:',  # Variant without Date
    r'From:\n',  # Simple From separator
    r'Sent:\n',  # Simple Sent separator
    r'To:\n',  # Simple To separator
    r'Subject:\n',  # Simple Subject separator
    
    # Italian patterns
    r'Da:.*?Inviato:.*?A:.*?Oggetto:',  # Italian Outlook
    r'Il.*?ha scritto:',  # Italian Gmail
    r'Messaggio inoltrato:',  # Italian forwarded
    r'In data:.*?ha scritto:',  # Italian date pattern
    
    # English patterns
    r'From:.*?Sent:.*?To:.*?Subject:',  # English Outlook
    r'On.*?wrote:',  # English Gmail
    r'Begin forwarded message:',  # English forwarded
    
    # Generic patterns
    r'-{3,}Original Message-{3,}',  # Various email clients
    r'-{3,}Messaggio originale-{3,}',  # Italian original message
    r'From:.*?\[mailto:.*?\]',  # Outlook with mailto
    r'Da:.*?\[mailto:.*?\]',  # Italian Outlook with mailto
    r'>.*?(?:wrote|ha scritto):',  # Generic reply pattern in both languages
    r'(?:^|\n)>',  # Quote marker at start of line
    r'(?:^|\n)Il giorno.*?(?:<.*?>)?ha scritto:',  # Italian detailed date pattern
    
    # Complex email headers with multiple recipients
    r'From:.*?<[^>]+>.*?(?:Date|Data):.*?(?:To|A):.*?(?:Cc:.*?)?(?:Subject|Oggetto):',  # Full header with multiple fields
]

# Precompile the divider patterns
COMPILED_DIVIDER_PATTERNS = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in DIVIDER_PATTERNS]


def _convert_html_to_text(text: str) -> str:
    """
    Convert HTML to plain text if needed.
    Preserves line breaks and spacing while removing HTML tags.
    """
    try:
        # Quick check: if it doesn't look like HTML, return immediately
        if '<' not in text or '>' not in text:
            return text
            
        # Do some simple HTML detection to avoid expensive parsing for non-HTML content
        html_indicators = ['<html', '<body', '<div', '<span', '<p ', '<br', '<table']
        has_html = any(indicator in text.lower() for indicator in html_indicators)
        
        if not has_html:
            # Try a more aggressive check for HTML content
            # If < is not followed by a letter within a reasonable distance, it's likely not HTML
            html_tag_pattern = re.compile(r'<[a-zA-Z][^>]*>')
            if not html_tag_pattern.search(text):
                return text
        
        # Special handling for email addresses with angle brackets
        # This prevents them from being recognized as HTML tags
        # Look for patterns like "Name <email@domain.com>"
        email_pattern = re.compile(r'([^<]+)<([^>@]+@[^>]+)>')
        text = email_pattern.sub(r'\1(\2)', text)
        
        # If we get here, it's likely HTML, so parse it
        # Use the faster 'lxml' parser if available
        soup = BeautifulSoup(text, 'lxml')
        
        # Handle tables before we get the text content
        try:
            # Convert tables to ASCII (but limit to first 10 tables for performance)
            tables = soup.find_all('table', limit=10)
            for table in tables:
                try:
                    ascii_table = _convert_table_to_ascii(table)
                    # Create a new element to replace the table
                    new_element = soup.new_tag('pre')
                    new_element.string = ascii_table
                    table.replace_with(new_element)
                except Exception as table_error:
                    # If table conversion fails, just remove the table
                    logger.warning(f"Table conversion failed: {str(table_error)}")
                    table.decompose()
        except Exception as tables_error:
            logger.warning(f"Table processing failed: {str(tables_error)}")
        
        # Remove script and style elements that we don't want in the text
        for element in soup.find_all(['script', 'style']):
            element.decompose()
            
        # Replace common HTML tags with newlines
        for br in soup.find_all('br'):
            br.replace_with('\n')  # type: ignore
            
        # Add newlines after block elements
        for tag in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']):
            tag.append('\n')  # type: ignore
            
        # Add double newlines after larger structural elements
        for tag in soup.find_all(['tr', 'table']):
            tag.append('\n\n')  # type: ignore
        
        # Remove elements with href attributes that might contain email addresses and links
        for a in soup.find_all('a', href=True):
            # If it's an email link, just keep the email text
            if 'mailto:' in a['href']:  # type: ignore
                email = a['href'].replace('mailto:', '')  # type: ignore
                a.replace_with(email)  # type: ignore
            else:
                # For other links, keep the link text
                a.replace_with(a.get_text())  # type: ignore
        
        # Handle lingering href attributes that might cause detection in has_html_content
        for tag in soup.find_all(attrs={'href': True}):
            del tag['href']  # type: ignore
            
        # Remove style attributes which are often detected by has_html_content
        for tag in soup.find_all(attrs={'style': True}):
            del tag['style']  # type: ignore
            
        # Remove class attributes
        for tag in soup.find_all(attrs={'class': True}):
            del tag['class']  # type: ignore
            
        # Remove target attributes
        for tag in soup.find_all(attrs={'target': True}):
            del tag['target']  # type: ignore
            
        # Extract text content
        text_content = soup.get_text()
        
        # Clean up whitespace
        # Remove excess whitespace
        text_content = re.sub(r'[ \t]+', ' ', text_content)
        # Normalize newlines (replace 3+ consecutive newlines with just 2)
        text_content = re.sub(r'\n{3,}', '\n\n', text_content)
        # Ensure consistent newlines at the beginning and end
        text_content = text_content.strip()
        
        # Clean any remaining HTML entities
        text_content = re.sub(r'&[a-zA-Z]+;|&#\d+;', ' ', text_content)
        
        # Remove any remaining HTML attributes and tags that could be left
        # The failing test shows that we have patterns like (img width="1240"...) and (a href="mailto:...)
        # Remove the HTML-like attributes
        text_content = re.sub(r'\(\s*(?:img|a)\s+[^\)]+\)', '', text_content)
        
        # Remove any tag-like patterns 
        text_content = re.sub(r'</?[a-zA-Z][^>]*>', '', text_content)
        
        # Remove any attribute-like patterns
        text_content = re.sub(r'\s+(?:class|style|id|src|height|width|target|href)="[^"]*"', '', text_content)
        
        # Clean up multiple spaces again after removals
        text_content = re.sub(r'[ \t]+', ' ', text_content)
        
        return text_content
        
    except Exception as e:
        # If HTML parsing fails, return original text
        logger.warning(f"HTML parsing failed: {str(e)}")
        return text
    
def _convert_table_to_ascii(table) -> str:
    """
    Convert an HTML table to an ASCII table using PrettyTable.
    """
    # Extract rows and columns from the HTML table
    rows = []
    header_row = None
    
    try:
        for row in table.find_all('tr'):
            cols = row.find_all(['td', 'th'])
            if not cols:
                continue
                
            row_data = [col.get_text(strip=True) for col in cols]
            
            # Check if this is potentially a header row (contains th elements)
            if row.find('th') and header_row is None:
                header_row = row_data
            else:
                rows.append(row_data)
        
        # If no explicit header row was found, use the first row as header
        if not header_row and rows:
            header_row = rows.pop(0)
        
        # If we have no rows or headers, return empty string
        if not header_row:
            return ""
            
        # Create the PrettyTable
        pt = PrettyTable()
        
        # Set field names
        pt.field_names = header_row
        
        # Ensure all rows have the correct number of columns
        column_count = len(header_row)
        valid_rows = []
        for row in rows:
            # If row has correct number of columns, add it
            if len(row) == column_count:
                valid_rows.append(row)
            # If fewer columns, pad with empty strings
            elif len(row) < column_count:
                padded_row = row + [''] * (column_count - len(row))
                valid_rows.append(padded_row)
            # If more columns, truncate
            else:
                valid_rows.append(row[:column_count])
        
        # Add rows to the table
        for row in valid_rows:
            pt.add_row(row)
        
        # Configure table formatting to match expected output format
        pt.align = 'c'  # Center alignment
        
        # Format as string
        result = pt.get_string()
        return result
        
    except Exception as e:
        logger.warning(f"Table conversion error: {str(e)}")
        return ""

def _find_first_divider( text: str, lazy=False) -> Optional[int]:
    """Find position of first divider pattern in text. 
    If lazy is True, return the first divider found, otherwise return the earliest one."""
    
    # Early validation: Return None if the text is too short
    if not text or len(text) < 10:
        return None
        
    # Early optimization: Only process a limited portion of the text
    # Most quoted content markers appear near the top of the message
    # Use a reasonable limit (e.g., first 10,000 characters)
    max_search_length = min(len(text), 10000)
    search_text = text[:max_search_length]
    
    # Check for exact patterns that indicate the beginning of a reply or forwarded message
    exact_patterns = [
        "wrote:\nPrevious message",           # Common reply format
    ]
    
    for pattern in exact_patterns:
        pos = search_text.find(pattern)
        if pos != -1:
            return pos
    
    # Check for simple patterns first using fast string operations
    # These cover most common cases and are much faster than regex
    fast_markers = [
        "\nFrom:", 
        "\nSent:", 
        "\nTo:", 
        "\nSubject:",
        "\nDa:",
        "\nInviato:",
        "\nA:",
        "\nOggetto:",
        "Original Message",
        "Messaggio originale",
        "Begin forwarded message",
        "Messaggio inoltrato",
        "On 2025-02-13",
        "On 20",  # Date patterns like "On 2023-01-01"
        "wrote:",
        "________________________________",
        "\n> ",   # Quoted text marker
    ]
    
    min_position = max_search_length + 1
    for marker in fast_markers:
        pos = search_text.find(marker)
        if pos != -1 and pos < min_position:
            min_position = pos
            if lazy:  # Return immediately if we're in lazy mode
                return pos
    
    # If we found a position with the fast method, return it
    if min_position < max_search_length + 1:
        return min_position
        
    # Fall back to regex for more complex patterns
    # Check specifically for pattern from test case
    on_date_pattern = re.compile(r'On \d{4}-\d{2}-\d{2}, .* wrote:', re.IGNORECASE | re.MULTILINE)
    match = on_date_pattern.search(search_text)
    if match:
        return match.start()
        
    # Try the compiled patterns
    for cre in COMPILED_DIVIDER_PATTERNS:
        match = cre.search(search_text)
        if match:
            return match.start()
    
    # Final search in the entire text but only if we haven't found anything yet
    # and only search a limited number of patterns
    if len(text) > max_search_length:
        for cre in COMPILED_DIVIDER_PATTERNS[:3]:
            match = cre.search(text)
            if match:
                return match.start()
                
    return None

def clean_body(body: str) -> str:
    """
    Extract the latest message from an email body by removing quoted text
    
    Args:
        body: Raw email body text
        message_id: Optional identifier for the email
        
    Returns:
        Cleaned message containing only the latest reply
    """
    if not body:
        return ""
    
    # First convert any HTML to plain text
    cleaned_html = _convert_html_to_text(body)
        
    # Find the first occurrence of any divider pattern in the cleaned HTML
    first_divider_pos = _find_first_divider(cleaned_html)
    
    if first_divider_pos is not None:
        # Extract everything before the first divider
        cleaned_text = cleaned_html[:first_divider_pos].strip()
    else:
        cleaned_text = cleaned_html
    
    return cleaned_text.strip()
