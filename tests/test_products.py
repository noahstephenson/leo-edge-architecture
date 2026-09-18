"""Tests for products module."""

def test_product_tier_exists():
    from leo_edge.products import ProductTier
    assert hasattr(ProductTier, "P0_METADATA")
    assert ProductTier.P0_METADATA == "P0_METADATA"

def test_product_dataclass_exists():
    import dataclasses
    from leo_edge.products import Product
    field_names = {f.name for f in dataclasses.fields(Product)}
    assert "tier" in field_names
