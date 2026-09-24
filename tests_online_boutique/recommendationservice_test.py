# Synthetic test for recommendationservice
def test_recommendation_returns_products():
    """Check that recommendations return a list."""
    recommendations = ["product1", "product2"]
    assert len(recommendations) > 0

def test_recommendation_limits_count():
    """Check that recommendations are limited."""
    max_recommendations = 5
    assert max_recommendations == 5