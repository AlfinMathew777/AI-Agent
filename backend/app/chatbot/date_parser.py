"""
Date Parser
Parses natural language dates to ISO format (YYYY-MM-DD)
Handles expressions like "March 15-17", "next Friday", "tomorrow", etc.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
import calendar


def parse_date_range(text: str, reference_date: Optional[datetime] = None) -> Optional[Tuple[str, str]]:
    """
    Parse natural language date expressions to ISO format
    
    Args:
        text: Natural language text containing dates
        reference_date: Reference date for relative expressions (defaults to today)
    
    Returns:
        Tuple of (check_in, check_out) in YYYY-MM-DD format, or None
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    text_lower = text.lower()
    
    # Pattern 1: "March 15-17" or "Mar 15-17"
    month_range_pattern = r'(\w+)\s+(\d{1,2})\s*-\s*(\d{1,2})'
    match = re.search(month_range_pattern, text_lower)
    if match:
        month_name, start_day, end_day = match.groups()
        month_num = _parse_month(month_name)
        if month_num:
            year = reference_date.year
            # If month has passed this year, assume next year
            if month_num < reference_date.month:
                year += 1
            
            try:
                check_in = datetime(year, month_num, int(start_day))
                check_out = datetime(year, month_num, int(end_day))
                return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
            except ValueError:
                pass
    
    # Pattern 2: "March 15 to March 17" or "Mar 15 to Mar 17"
    month_to_pattern = r'(\w+)\s+(\d{1,2})\s+to\s+(\w+)\s+(\d{1,2})'
    match = re.search(month_to_pattern, text_lower)
    if match:
        month1, day1, month2, day2 = match.groups()
        month1_num = _parse_month(month1)
        month2_num = _parse_month(month2)
        if month1_num and month2_num:
            year = reference_date.year
            if month1_num < reference_date.month:
                year += 1
            
            try:
                check_in = datetime(year, month1_num, int(day1))
                check_out = datetime(year, month2_num, int(day2))
                return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
            except ValueError:
                pass
    
    # Pattern 3: "2024-03-15 to 2024-03-17" (ISO format)
    iso_pattern = r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})'
    match = re.search(iso_pattern, text)
    if match:
        return (match.group(1), match.group(2))
    
    # Pattern 4: Relative dates like "tomorrow", "next week"
    relative_match = _parse_relative_dates(text_lower, reference_date)
    if relative_match:
        return relative_match
    
    # Pattern 5: "15th to 17th of March"
    ordinal_pattern = r'(\d{1,2})(?:st|nd|rd|th)?\s+to\s+(\d{1,2})(?:st|nd|rd|th)?\s+(?:of\s+)?(\w+)'
    match = re.search(ordinal_pattern, text_lower)
    if match:
        day1, day2, month_name = match.groups()
        month_num = _parse_month(month_name)
        if month_num:
            year = reference_date.year
            if month_num < reference_date.month:
                year += 1
            
            try:
                check_in = datetime(year, month_num, int(day1))
                check_out = datetime(year, month_num, int(day2))
                return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
            except ValueError:
                pass
    
    # Pattern 6: Extract any YYYY-MM-DD dates and use first two
    iso_dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
    if len(iso_dates) >= 2:
        return (iso_dates[0], iso_dates[1])
    
    return None


def _parse_month(month_str: str) -> Optional[int]:
    """Convert month name to month number"""
    month_str = month_str.lower().strip()
    
    months = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12
    }
    
    return months.get(month_str)


def _parse_relative_dates(text: str, reference_date: datetime) -> Optional[Tuple[str, str]]:
    """Parse relative date expressions"""
    
    # Tomorrow
    if 'tomorrow' in text:
        check_in = reference_date + timedelta(days=1)
        check_out = check_in + timedelta(days=1)  # Default 1 night
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # Today / Tonight
    if 'today' in text or 'tonight' in text:
        check_in = reference_date
        check_out = reference_date + timedelta(days=1)
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # Next week
    if 'next week' in text:
        days_ahead = 7 - reference_date.weekday()  # Days until next Monday
        check_in = reference_date + timedelta(days=days_ahead)
        check_out = check_in + timedelta(days=2)  # Default 2 nights
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # Next [weekday]
    weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for i, day in enumerate(weekdays):
        if f'next {day}' in text:
            days_ahead = (i - reference_date.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            check_in = reference_date + timedelta(days=days_ahead)
            check_out = check_in + timedelta(days=1)
            return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # This weekend
    if 'this weekend' in text or 'weekend' in text:
        days_until_friday = (4 - reference_date.weekday()) % 7
        if days_until_friday == 0 and reference_date.hour > 12:
            days_until_friday = 7
        check_in = reference_date + timedelta(days=days_until_friday)
        check_out = check_in + timedelta(days=2)  # Friday to Sunday
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # X days from now
    days_pattern = r'(\d+)\s+days?\s+(?:from\s+now|ahead)'
    match = re.search(days_pattern, text)
    if match:
        num_days = int(match.group(1))
        check_in = reference_date + timedelta(days=num_days)
        check_out = check_in + timedelta(days=1)
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    # X nights
    nights_pattern = r'(\d+)\s+nights?'
    match = re.search(nights_pattern, text)
    if match:
        num_nights = int(match.group(1))
        # Look for check-in date in text
        check_in = reference_date + timedelta(days=1)  # Default tomorrow
        check_out = check_in + timedelta(days=num_nights)
        return (check_in.strftime("%Y-%m-%d"), check_out.strftime("%Y-%m-%d"))
    
    return None


def extract_guest_count(text: str) -> int:
    """Extract number of guests from text"""
    text_lower = text.lower()
    
    # Pattern: "2 guests", "for 3 people", "party of 4"
    patterns = [
        r'(\d+)\s+(?:guests?|people|persons?)',
        r'party\s+of\s+(\d+)',
        r'for\s+(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return int(match.group(1))
    
    # Default to 2 if not specified
    return 2


def extract_room_type(text: str) -> Optional[str]:
    """Extract room type from text"""
    text_lower = text.lower()
    
    # Map common phrases to room types
    room_mappings = {
        'deluxe': 'deluxe_king',
        'king': 'deluxe_king',
        'queen': 'standard_queen',
        'double': 'standard_double',
        'twin': 'twin',
        'suite': 'executive_suite',
        'executive': 'executive_suite',
        'presidential': 'presidential'
    }
    
    for keyword, room_type in room_mappings.items():
        if keyword in text_lower:
            return room_type
    
    return None
