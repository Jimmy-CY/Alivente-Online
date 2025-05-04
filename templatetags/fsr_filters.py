from django import template
from datetime import date

register = template.Library()

@register.filter
def filter_by_prop(issues, prop_name):
    """Filter issues by property name"""
    if not issues:
        return []
    return [issue for issue in issues if issue.get('prop_name') == prop_name]

@register.filter
def filter_by_status(issues, status):
    """Filter issues by status with date handling"""
    if not issues:
        return []
    
    if status == 'Resolved':
        return [
            issue for issue in issues 
            if issue.get('issues_status') == status
            and issue.get('issues_resolution_date') != date(1900, 1, 1)
        ]
    return [issue for issue in issues if issue.get('issues_status') == status]

@register.filter
def unique_issues(issues):
    """Remove duplicate issues based on heading/description"""
    if not issues:
        return []
    
    seen = set()
    unique = []
    for issue in issues:
        key = (issue.get('issues_heading'), issue.get('issues_description'))
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return unique