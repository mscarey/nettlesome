from nettlesome.statements import Assertion


class TestSpec:
    def test_make_json_spec(self):
        schema = Assertion.model_json_schema()
        ref = schema["$defs"]["Assertion"]["properties"]["statement"]["$ref"]
        ent_ref = schema["$defs"]["Assertion"]["properties"]["authority"]["anyOf"][0][
            "$ref"
        ]
        assert ref == "#/$defs/Statement"
        assert ent_ref == "#/$defs/Entity"
