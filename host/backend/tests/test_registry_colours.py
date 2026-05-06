"""
Unit tests for registry.colour_palette — is_valid_colour and ColourAllocator.
EP-03, US-01 AC-2.
"""

import pytest

from ee_game_backend.registry.colour_palette import (
    COLOUR_PALETTE,
    ColourAllocator,
    is_valid_colour,
)
from ee_game_backend.registry.exceptions import CapacityError


class TestIsValidColour:
    def test_accepts_exact_palette_entry(self):
        for colour in COLOUR_PALETTE:
            assert is_valid_colour(colour), f"Expected {colour!r} to be valid"

    def test_accepts_lowercase_variant(self):
        assert is_valid_colour(COLOUR_PALETTE[0].lower())

    def test_accepts_mixed_case_variant(self):
        # "#e6194b" vs "#E6194B"
        mixed = COLOUR_PALETTE[0][0] + COLOUR_PALETTE[0][1:].lower()
        assert is_valid_colour(mixed)

    def test_rejects_arbitrary_hex(self):
        assert not is_valid_colour("#FFFFFF")
        assert not is_valid_colour("#000000")

    def test_rejects_empty_string(self):
        assert not is_valid_colour("")

    def test_rejects_colour_name(self):
        assert not is_valid_colour("red")

    def test_palette_has_exactly_20_entries(self):
        assert len(COLOUR_PALETTE) == 20

    def test_palette_entries_are_unique(self):
        assert len(COLOUR_PALETTE) == len(set(COLOUR_PALETTE))


class TestColourAllocator:
    def test_allocate_returns_first_available(self):
        allocator = ColourAllocator()
        colour = allocator.allocate(exclude=[])
        assert colour == COLOUR_PALETTE[0]

    def test_allocate_skips_excluded(self):
        allocator = ColourAllocator()
        colour = allocator.allocate(exclude=[COLOUR_PALETTE[0]])
        assert colour == COLOUR_PALETTE[1]

    def test_allocate_skips_multiple_excluded(self):
        allocator = ColourAllocator()
        excluded = COLOUR_PALETTE[:5]
        colour = allocator.allocate(exclude=excluded)
        assert colour == COLOUR_PALETTE[5]

    def test_allocate_raises_capacity_error_when_all_taken(self):
        allocator = ColourAllocator()
        with pytest.raises(CapacityError):
            allocator.allocate(exclude=COLOUR_PALETTE)

    def test_allocate_is_case_insensitive_for_exclusion(self):
        allocator = ColourAllocator()
        # Exclude first colour in lowercase — should still be skipped.
        colour = allocator.allocate(exclude=[COLOUR_PALETTE[0].lower()])
        assert colour == COLOUR_PALETTE[1]

    def test_release_does_not_raise(self):
        allocator = ColourAllocator()
        allocator.release(COLOUR_PALETTE[0])  # Must not raise.

    def test_allocate_single_remaining(self):
        allocator = ColourAllocator()
        excluded = COLOUR_PALETTE[:-1]
        colour = allocator.allocate(exclude=excluded)
        assert colour == COLOUR_PALETTE[-1]
