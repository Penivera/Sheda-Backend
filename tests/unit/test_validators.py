"""Unit tests for validators."""

import pytest
from app.utils.validators import (
    ValidatorMixin,
    PropertyValidators,
    TransactionValidators,
)


class TestValidatorMixin:
    """Test base validator functions."""

    def test_validate_ethereum_address_valid(self):
        """Test valid Ethereum address."""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f73f2B"
        result = ValidatorMixin.validate_ethereum_address(address)
        assert result == address.lower()

    def test_validate_ethereum_address_invalid_format(self):
        """Test invalid Ethereum address format."""
        with pytest.raises(ValueError, match="Invalid Ethereum address format"):
            ValidatorMixin.validate_ethereum_address("not_an_address")

    def test_validate_ethereum_address_too_short(self):
        """Test Ethereum address too short."""
        with pytest.raises(ValueError, match="Invalid Ethereum address format"):
            ValidatorMixin.validate_ethereum_address("0x12345")

    def test_validate_blockchain_hash_valid(self):
        """Test valid blockchain hash."""
        hash_val = "0x" + "a" * 64
        result = ValidatorMixin.validate_blockchain_hash(hash_val)
        assert result == hash_val.lower()

    def test_validate_blockchain_hash_invalid(self):
        """Test invalid blockchain hash."""
        with pytest.raises(ValueError, match="Invalid blockchain hash format"):
            ValidatorMixin.validate_blockchain_hash("0x12345")

    def test_validate_bedroom_count_valid(self):
        """Test valid bedroom count."""
        result = ValidatorMixin.validate_bedroom_count(3)
        assert result == 3

    def test_validate_bedroom_count_zero(self):
        """Test bedroom count of zero."""
        with pytest.raises(ValueError, match="Bedroom count must be at least 1"):
            ValidatorMixin.validate_bedroom_count(0)

    def test_validate_bedroom_count_negative(self):
        """Test negative bedroom count."""
        with pytest.raises(ValueError, match="Bedroom count must be at least 1"):
            ValidatorMixin.validate_bedroom_count(-1)

    def test_validate_bedroom_count_too_high(self):
        """Test bedroom count exceeds maximum."""
        with pytest.raises(ValueError, match="Bedroom count too high"):
            ValidatorMixin.validate_bedroom_count(51)

    def test_validate_bathroom_count_valid(self):
        """Test valid bathroom count."""
        result = ValidatorMixin.validate_bathroom_count(2)
        assert result == 2

    def test_validate_bathroom_count_invalid(self):
        """Test invalid bathroom count."""
        with pytest.raises(ValueError):
            ValidatorMixin.validate_bathroom_count(0)


class TestPropertyValidators:
    """Test property-specific validators."""

    def test_validate_price_valid(self):
        """Test valid price validation."""
        result = PropertyValidators.validate_price(100.50)
        assert result == 100.50

    def test_validate_price_negative(self):
        """Test negative price."""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            PropertyValidators.validate_price(-100)

    def test_validate_price_zero(self):
        """Test zero price."""
        with pytest.raises(ValueError, match="Price must be greater than zero"):
            PropertyValidators.validate_price(0)

    def test_validate_price_too_high(self):
        """Test price exceeds max value."""
        with pytest.raises(ValueError, match="Price exceeds maximum"):
            PropertyValidators.validate_price(2**128)

    def test_validate_title_valid(self):
        """Test valid title."""
        result = PropertyValidators.validate_title("Beautiful 3BR Apartment")
        assert result == "Beautiful 3BR Apartment"

    def test_validate_title_too_short(self):
        """Test title too short."""
        with pytest.raises(ValueError, match="Title must be at least 5 characters"):
            PropertyValidators.validate_title("Bad")

    def test_validate_title_too_long(self):
        """Test title too long."""
        long_title = "A" * 201
        with pytest.raises(ValueError, match="Title cannot exceed 200 characters"):
            PropertyValidators.validate_title(long_title)

    def test_validate_description_valid(self):
        """Test valid description."""
        desc = "A" * 100
        result = PropertyValidators.validate_description(desc)
        assert result == desc

    def test_validate_description_too_short(self):
        """Test description too short."""
        with pytest.raises(
            ValueError, match="Description must be at least 20 characters"
        ):
            PropertyValidators.validate_description("Too short")

    def test_validate_description_too_long(self):
        """Test description too long."""
        long_desc = "A" * 5001
        with pytest.raises(
            ValueError, match="Description cannot exceed 5000 characters"
        ):
            PropertyValidators.validate_description(long_desc)

    def test_validate_location_valid(self):
        """Test valid location."""
        result = PropertyValidators.validate_location("Lagos, Nigeria")
        assert result == "Lagos, Nigeria"

    def test_validate_location_too_short(self):
        """Test location too short."""
        with pytest.raises(ValueError):
            PropertyValidators.validate_location("LA")


class TestTransactionValidators:
    """Test transaction-specific validators."""

    def test_validate_bid_amount_valid(self):
        """Test valid bid amount."""
        result = TransactionValidators.validate_bid_amount(1000000)
        assert result == 1000000

    def test_validate_bid_amount_negative(self):
        """Test negative bid amount."""
        with pytest.raises(ValueError, match="Bid amount must be positive"):
            TransactionValidators.validate_bid_amount(-1000)

    def test_validate_bid_amount_zero(self):
        """Test zero bid amount."""
        with pytest.raises(ValueError, match="Bid amount must be positive"):
            TransactionValidators.validate_bid_amount(0)

    def test_validate_transaction_status_valid(self):
        """Test valid transaction status."""
        valid_statuses = ["pending", "completed", "failed", "cancelled"]
        for status in valid_statuses:
            result = TransactionValidators.validate_transaction_status(status)
            assert result == status

    def test_validate_transaction_status_invalid(self):
        """Test invalid transaction status."""
        with pytest.raises(ValueError, match="Invalid transaction status"):
            TransactionValidators.validate_transaction_status("invalid_status")


class TestCacheKeys:
    """Test cache key generation."""

    def test_user_profile_key(self):
        """Test user profile key generation."""
        from app.utils.cache_keys import user_profile_key

        assert user_profile_key(123) == "user:profile:123"

    def test_property_detail_key(self):
        """Test property detail key generation."""
        from app.utils.cache_keys import property_detail_key

        assert property_detail_key(456) == "property:detail:456"

    def test_property_feed_key(self):
        """Test property feed key generation."""
        from app.utils.cache_keys import property_feed_key

        assert property_feed_key(page=1) == "property:feed:p1"
        assert (
            property_feed_key(page=2, filters_hash="abc123")
            == "property:feed:p2:abc123"
        )

    def test_generate_filter_hash(self):
        """Test filter hash generation."""
        from app.utils.cache_keys import generate_filter_hash

        filters1 = {"price_min": 1000, "location": "Lagos"}
        filters2 = {"location": "Lagos", "price_min": 1000}  # Same but different order

        hash1 = generate_filter_hash(filters1)
        hash2 = generate_filter_hash(filters2)

        # Should be identical (order-independent)
        assert hash1 == hash2
        assert len(hash1) == 32  # MD5 hash length
