"""
Unit tests for registry.username_generator — UsernameGenerator.
EP-03, US-01 AC-2.
"""


from ee_game_backend.registry.username_generator import (
    ADJECTIVES,
    NOUNS,
    UsernameGenerator,
)


class TestUsernameGeneratorBasics:
    def test_generate_returns_string(self):
        gen = UsernameGenerator(seed=42)
        name = gen.generate(exclude=[])
        assert isinstance(name, str)

    def test_generate_returns_pascal_case_combination(self):
        """Every generated name should be an adjective + noun (PascalCase)."""
        gen = UsernameGenerator(seed=0)
        name = gen.generate(exclude=[])
        # At least one of the known adjectives/nouns must appear in the name.
        matched_adj = any(name.startswith(adj) for adj in ADJECTIVES)
        assert matched_adj, f"Name {name!r} does not start with a known adjective"
        suffix = name[len(next(adj for adj in ADJECTIVES if name.startswith(adj))):]
        assert suffix in NOUNS, f"Suffix {suffix!r} is not a known noun"

    def test_pool_size_is_100(self):
        """Total pool must be len(ADJECTIVES) * len(NOUNS) == 100."""
        assert len(ADJECTIVES) == 10
        assert len(NOUNS) == 10


class TestUsernameGeneratorExclusion:
    def test_generate_never_returns_excluded_name(self):
        gen = UsernameGenerator(seed=7)
        first = gen.generate(exclude=[])
        # Regenerate from same seed; first name must be skipped.
        gen2 = UsernameGenerator(seed=7)
        second = gen2.generate(exclude=[first])
        assert second != first

    def test_generate_skips_all_excluded(self):
        gen = UsernameGenerator(seed=1)
        # Pre-build 50 names so we know exactly which ones are "taken".
        taken: list[str] = []
        for _ in range(50):
            taken.append(gen.generate(exclude=taken))
        # Next name must not be in taken.
        next_name = gen.generate(exclude=taken)
        assert next_name not in taken


class TestUsernameGeneratorPoolExhaustion:
    def test_generate_100_unique_names(self):
        gen = UsernameGenerator(seed=99)
        names: list[str] = []
        for _ in range(100):
            name = gen.generate(exclude=names)
            assert name not in names, f"Duplicate name {name!r} after {len(names)} draws"
            names.append(name)
        assert len(names) == 100

    def test_generate_continues_after_pool_exhausted(self):
        """After 100 draws the generator must not raise — it appends a suffix."""
        gen = UsernameGenerator(seed=5)
        names: list[str] = []
        for _ in range(100):
            names.append(gen.generate(exclude=names))
        # 101st call must succeed and return something not in names.
        extra = gen.generate(exclude=names)
        assert extra not in names
        assert isinstance(extra, str)
        assert len(extra) > 0

    def test_generate_101_are_all_unique(self):
        gen = UsernameGenerator(seed=3)
        names: list[str] = []
        for _ in range(101):
            name = gen.generate(exclude=names)
            assert name not in names
            names.append(name)
        assert len(set(names)) == 101
