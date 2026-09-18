"""Registry-load strictness — the service must fail fast at boot when
MODEL_REGISTRY_PATH contains a malformed catalog, instead of silently
starting with a partial one (the old behavior logged and dropped bad
entries, and duplicate ids silently overwrote each other).

Tolerated modes stay tolerated: unset path and missing file start empty.
Everything else — invalid JSON, non-object root, missing/non-list
"models", a malformed entry, a duplicate id — raises RegistryConfigError,
and the load is atomic (nothing is registered unless every entry
validated; a failed reload never destroys a previously loaded catalog).
"""

import json

import pytest

from app.config import ModelRouterConfig
from app.registry import ModelRegistry, RegistryConfigError


def _write(tmp_path, payload):
    """Write a registry file; payload is a JSON string or an object."""
    text = payload if isinstance(payload, str) else json.dumps(payload)
    p = tmp_path / "models.json"
    p.write_text(text, encoding="utf-8")
    return str(p)


def _registry(path):
    return ModelRegistry(ModelRouterConfig(model_registry_path=path))


def _good_model(i=0):
    return {
        "id": f"model-{i}",
        "provider": "vllm",
        "total_parameters_billions": 7.0,
        "context_window": 32768,
        "capabilities": ["coding"],
        "max_classification": "CONFIDENTIAL",
        "is_available": True,
    }


class TestToleratedModesStillTolerated:
    async def test_unset_path_starts_empty(self, tmp_path):
        reg = _registry("")
        await reg.load()
        assert reg.list_all() == []

    async def test_missing_file_starts_empty(self, tmp_path):
        reg = _registry(str(tmp_path / "nope.json"))
        await reg.load()
        assert reg.list_all() == []

    async def test_valid_catalog_loads_every_entry(self, tmp_path):
        path = _write(tmp_path, {"models": [_good_model(0), _good_model(1)]})
        reg = _registry(path)
        await reg.load()
        assert sorted(m.id for m in reg.list_all()) == ["model-0", "model-1"]


class TestStrictFailures:
    async def test_invalid_json_fails_fast(self, tmp_path):
        path = _write(tmp_path, "{not json at all")
        reg = _registry(path)
        with pytest.raises(RegistryConfigError, match="not valid JSON"):
            await reg.load()

    async def test_non_object_root_fails_fast(self, tmp_path):
        path = _write(tmp_path, "[1, 2, 3]")
        reg = _registry(path)
        with pytest.raises(RegistryConfigError, match="JSON object"):
            await reg.load()

    async def test_missing_models_key_fails_fast(self, tmp_path):
        path = _write(tmp_path, {"not_models": []})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError, match='"models" array'):
            await reg.load()

    async def test_non_list_models_fails_fast(self, tmp_path):
        path = _write(tmp_path, {"models": {"id": "x"}})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError, match='"models" array'):
            await reg.load()

    async def test_malformed_entry_names_index_and_id(self, tmp_path):
        bad = _good_model(0)
        bad["provider"] = "not-a-provider"
        path = _write(tmp_path, {"models": [_good_model(1), bad]})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError) as err:
            await reg.load()
        message = str(err.value)
        assert "models[1]" in message and "model-0" in message

    async def test_malformed_non_dict_entry_included_in_error(self, tmp_path):
        path = _write(tmp_path, {"models": ["not-a-dict"]})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError) as err:
            await reg.load()
        assert "models[0]" in str(err.value)

    async def test_duplicate_ids_fail_fast_with_both_indexes(self, tmp_path):
        dup = _good_model(0)
        path = _write(tmp_path, {"models": [dup, _good_model(1), dup]})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError) as err:
            await reg.load()
        message = str(err.value)
        assert "duplicate model id 'model-0'" in message
        assert "models[0]" in message and "models[2]" in message


class TestAtomicity:
    async def test_failed_load_never_leaves_half_loaded_registry(self, tmp_path):
        path = _write(tmp_path, {"models": [_good_model(0), "junk"]})
        reg = _registry(path)
        with pytest.raises(RegistryConfigError):
            await reg.load()
        assert reg.list_all() == []

    async def test_failed_reload_preserves_previously_loaded_catalog(self, tmp_path):
        good = tmp_path / "good.json"
        good.write_text(json.dumps({"models": [_good_model(0)]}), encoding="utf-8")
        reg = _registry(str(good))
        await reg.load()
        assert len(reg.list_all()) == 1

        bad = _write(tmp_path, {"models": [_good_model(9), {"id": "x"}]})
        reg2 = _registry(bad)
        with pytest.raises(RegistryConfigError):
            await reg2.load()
        # The failing file never touched the previously loaded registry.
        assert sorted(m.id for m in reg.list_all()) == ["model-0"]
