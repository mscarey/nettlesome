from nettlesome.spec import make_spec
from nettlesome.schemas import AssertionSchema


class TestSpec:
    def test_make_yaml_spec(self):
        spec = make_spec(AssertionSchema)
        as_yaml = spec.to_yaml()
        assert "$ref: '#/components/schemas/Predicate'" in as_yaml
