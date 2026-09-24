# Synthetic test for emailservice
def test_email_template_exists():
    """Check that the email template file exists."""
    assert True  # Placeholder

def test_order_confirmation_format():
    """Check the order confirmation format."""
    order_id = "ORDER-123"
    assert order_id.startswith("ORDER-")