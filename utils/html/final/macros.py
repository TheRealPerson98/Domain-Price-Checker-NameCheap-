def render_template(template_str, context):
    """
    Simple template rendering function that replaces {{key}} with values from context.
    
    Args:
        template_str (str): Template string with {{placeholders}}
        context (dict): Dictionary of values to replace placeholders
        
    Returns:
        str: Rendered template with placeholders replaced
    """
    result = template_str
    for key, value in context.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    return result


def get_status_info(price):
    """
    Get the status class and text based on price.
    
    Args:
        price (str): Price string from domain check
        
    Returns:
        tuple: (status_class, status_text)
    """
    if price.startswith("Unavailable"):
        return "status-unavailable", "Unavailable"
    elif price.startswith("Error"):
        return "status-error", "Error"
    else:
        return "status-available", "Available"


def count_statuses(results):
    """
    Count the number of domains in each status category.
    
    Args:
        results (dict): Domain results dictionary
        
    Returns:
        tuple: (available_count, unavailable_count, error_count)
    """
    available_count = 0
    unavailable_count = 0
    error_count = 0
    
    for _, price in results.items():
        if price.startswith("Unavailable"):
            unavailable_count += 1
        elif price.startswith("Error"):
            error_count += 1
        else:
            available_count += 1
            
    return available_count, unavailable_count, error_count 