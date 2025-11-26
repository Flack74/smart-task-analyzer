def validate_task(task):
    """Validate task data structure."""
    errors = {}
    
    if not isinstance(task.get('title'), str) or not task.get('title'):
        errors['title'] = 'Title is required and must be a string.'
    
    if 'estimated_hours' not in task:
        errors['estimated_hours'] = 'Estimated hours is required.'
    else:
        try:
            hours = float(task['estimated_hours'])
            if hours < 0:
                errors['estimated_hours'] = 'Estimated hours must be >= 0.'
        except (ValueError, TypeError):
            errors['estimated_hours'] = 'Estimated hours must be a number.'
    
    if 'importance' not in task:
        errors['importance'] = 'Importance is required.'
    else:
        try:
            imp = int(task['importance'])
            if imp < 1 or imp > 10:
                errors['importance'] = 'Importance must be between 1 and 10.'
        except (ValueError, TypeError):
            errors['importance'] = 'Importance must be an integer.'
    
    if task.get('due_date') and not isinstance(task['due_date'], str):
        errors['due_date'] = 'Due date must be a string (YYYY-MM-DD).'
    
    if task.get('dependencies') and not isinstance(task['dependencies'], list):
        errors['dependencies'] = 'Dependencies must be a list.'
    
    return errors
