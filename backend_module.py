


def summarize_text(text):
    """
    Returns a simple summary of the input text:
    the first 100 characters plus "..." if text is longer.
    """
    summary = text[:100] + ("..." if len(text) > 100 else "")
    return summary

def simplify_text(text):
    """
    Returns a simplified version of the input text.
    This example converts text to lowercase and removes extra spaces.
    """
    simplified = " ".join(text.lower().split())
    return simplified
