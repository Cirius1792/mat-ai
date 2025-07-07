"""
Unit tests for the configuration module in matai_v2.
"""
import os
import sys
import pytest
import yaml

# Ensure src directory is on path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from matai_v2.configuration import (
    OutlookConfig,
    TrelloConfig,
    EmailFilter,
    DatabaseConfig,
    LLMConfig,
    Config,
    save_config_to_yaml,
    load_config_from_yaml,
)


def test_dataclass_defaults_and_values():
    # OutlookConfig defaults and override
    oc = OutlookConfig()
    assert oc.tenant_id == ""
    assert oc.client_id == ""
    assert oc.client_secret == ""
    assert oc.redirect_uri == ""
    oc2 = OutlookConfig(tenant_id="t", client_id="cid", client_secret="sec", redirect_uri="uri")
    assert oc2.tenant_id == "t"
    assert oc2.client_id == "cid"
    assert oc2.client_secret == "sec"
    assert oc2.redirect_uri == "uri"

    # TrelloConfig defaults and override
    tc = TrelloConfig()
    assert tc.api_key == ""
    assert tc.api_token == ""
    assert tc.board == ""
    tc2 = TrelloConfig(api_key="k", api_token="tok", board="b")
    assert tc2.api_key == "k"
    assert tc2.api_token == "tok"
    assert tc2.board == "b"

    # EmailFilter defaults and override
    fc = EmailFilter()
    assert isinstance(fc.recipients, list) and fc.recipients == []
    fc2 = EmailFilter(recipients=["a@example.com", "b@example.com"])
    assert fc2.recipients == ["a@example.com", "b@example.com"]

    # DatabaseConfig default and override
    db = DatabaseConfig()
    assert db.path == "matai.db"
    db2 = DatabaseConfig(path="custom.db")
    assert db2.path == "custom.db"

    # LLMConfig defaults and override
    llm = LLMConfig()
    assert llm.host == ""
    assert llm.model == ""
    assert llm.api_key == ""
    llm2 = LLMConfig(host="h", model="m", api_key="k")
    assert llm2.host == "h"
    assert llm2.model == "m"
    assert llm2.api_key == "k"


def test_config_to_dict_default_keys_and_values():
    cfg = Config()
    as_dict = cfg.to_dict()
    # to_dict only includes database, outlook_config, trello_config
    assert set(as_dict.keys()) == {"database", "outlook_config", "trello_config", "llm_config", "filters"}
    # Values match underlying dataclasses
    assert as_dict["database"] == cfg.database.__dict__
    assert as_dict["outlook_config"] == cfg.outlook_config.__dict__
    assert as_dict["trello_config"] == cfg.trello_config.__dict__
    assert as_dict["llm_config"] == cfg.llm_config.__dict__
    assert as_dict["filters"] == cfg.filters.__dict__


def test_config_from_dict_minimal_and_full():
    # Minimal dict (defaults)
    minimal = {"database": {}, "outlook_config": {}, "trello_config": {}}
    cfg_min = Config.from_dict(minimal)
    assert isinstance(cfg_min, Config)
    # Defaults preserved
    assert cfg_min.database.path == "matai.db"
    assert cfg_min.outlook_config.client_id == ""
    assert cfg_min.trello_config.api_key == ""
    assert isinstance(cfg_min.llm_config, LLMConfig)
    assert cfg_min.llm_config.host == ""

    # Full dict (custom values)
    full = {
        "database": {"path": "db2.sqlite"},
        "outlook_config": {"tenant_id": "t", "client_id": "c", "client_secret": "s", "redirect_uri": "ru"},
        "trello_config": {"api_key": "k", "api_token": "tok", "board": "b"},
        "llm_config": {"host": "h", "model": "m", "api_key": "ak", },
    }
    cfg_full = Config.from_dict(full)
    assert cfg_full.database.path == "db2.sqlite"
    assert cfg_full.outlook_config.tenant_id == "t"
    assert cfg_full.outlook_config.client_id == "c"
    assert cfg_full.outlook_config.client_secret == "s"
    assert cfg_full.outlook_config.redirect_uri == "ru"
    assert cfg_full.trello_config.api_key == "k"
    assert cfg_full.trello_config.api_token == "tok"
    assert cfg_full.trello_config.board == "b"
    assert cfg_full.llm_config.host == "h"
    assert cfg_full.llm_config.model == "m"
    assert cfg_full.llm_config.api_key == "ak"


@pytest.mark.parametrize("missing", ["outlook_config", "trello_config"])
def test_config_from_dict_missing_required_raises(missing):
    data = {"database": {}}
    # Leave out required section
    with pytest.raises(KeyError):
        Config.from_dict({**data, **{k: {} for k in ["outlook_config", "trello_config"] if k != missing}})


def test_save_config_to_yaml_type_error(tmp_path):
    # Passing non-Config should raise
    file_path = tmp_path / "cfg.yaml"
    with pytest.raises(TypeError):
        save_config_to_yaml("not_a_config", file_path=str(file_path))  # type: ignore[reportArgumentType]


def test_save_and_load_config_yaml(tmp_path):
    # Save default config and reload
    cfg = Config()
    file_path = tmp_path / "cfg.yaml"
    save_config_to_yaml(cfg, file_path=str(file_path))
    # File content matches to_dict
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    assert data == cfg.to_dict()
    # load back
    loaded = load_config_from_yaml(file_path=str(file_path))
    assert isinstance(loaded, Config)
    # Core sections preserved
    assert loaded.database.path == cfg.database.path
    assert loaded.outlook_config.__dict__ == cfg.outlook_config.__dict__
    assert loaded.trello_config.__dict__ == cfg.trello_config.__dict__
    # llm_config not persisted in to_dict, so defaults
    assert isinstance(loaded.llm_config, LLMConfig)
    assert loaded.llm_config.host == ""


def test_load_config_with_llm_section(tmp_path):
    # Manually create YAML with llm_config
    manual = {
        "database": {"path": "d.sqlite"},
        "outlook_config": {},
        "trello_config": {},
        "llm_config": {"host": "h2", "model": "m2", "api_key": "ak2", },
    }
    file_path = tmp_path / "man.yaml"
    with open(file_path, 'w') as f:
        yaml.dump(manual, f)
    loaded = load_config_from_yaml(file_path=str(file_path))
    assert loaded.database.path == "d.sqlite"
    assert loaded.llm_config.host == "h2"
    assert loaded.llm_config.model == "m2"
    assert loaded.llm_config.api_key == "ak2"


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config_from_yaml(file_path="no_such_file.yaml")


def test_load_config_invalid_yaml(tmp_path):
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("not: [unbalanced")
    with pytest.raises(yaml.YAMLError):
        load_config_from_yaml(file_path=str(bad_file))
