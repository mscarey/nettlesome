from nettlesome.statements import Assertion


class TestSpec:
    def test_make_json_spec(self):
        schema = Assertion.schema()
        ref = schema["definitions"]["Assertion"]["properties"]["statement"]["$ref"]
        ent_ref = schema["definitions"]["Assertion"]["properties"]["authority"]["$ref"]
        assert ref == "#/definitions/Statement"
        assert ent_ref == "#/definitions/Entity"
