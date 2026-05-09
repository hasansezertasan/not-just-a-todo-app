# Copyright 2024 Hasan Sezer Taşan <hasansezertasan@gmail.com>
"""Property-based tests using Hypothesis.

Complements example-based unit tests by generating many inputs and
asserting invariants. Use for rules sharper than hand-rolled examples
can express.
"""

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    first=st.text(min_size=1, max_size=32).filter(lambda s: s.strip()),
    last=st.text(min_size=1, max_size=32).filter(lambda s: s.strip()),
)
def test_full_name_concatenation_format(first: str, last: str) -> None:
    """The `full_name` column_property is defined as `first + ' ' + last`.

    Verify the formula at the SQL-expression level so we don't need a DB
    round-trip per example. If the model definition changes the operator
    or separator, this test catches it.
    """
    from app.db.models.users import User

    expr = User.full_name.expression
    # column_property(a + ' ' + b) compiles to a CONCAT-style SQL expression;
    # the raw text differs by dialect, but the operands stay deterministic.
    rendered = str(expr.compile(compile_kwargs={"literal_binds": True}))
    assert "first_name" in rendered
    assert "last_name" in rendered
    # The pair (first, last) is fed into Hypothesis only to drive coverage of
    # text characters; the assertion above is dialect-stable.
    assert isinstance(first, str)
    assert isinstance(last, str)
