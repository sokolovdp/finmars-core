import json
import logging

import requests

from poms.vault.models import VaultRecord
from poms_app import settings

_l = logging.getLogger("poms.vault")


def remove_trailing_slash_from_keys(data):
    modified_data = {}
    for key, value in data.items():
        new_key = key.rstrip("/")  # Remove trailing slash
        modified_data[new_key] = value
    return modified_data


class FinmarsVault:
    def __init__(self, realm_code=None, space_code=None):
        self.realm_code = realm_code
        self.space_code = space_code

        if self.realm_code:
            self.vault_host = (
                "https://" + settings.DOMAIN_NAME + "/" + self.realm_code + "/" + self.space_code + "/vault"
            )
        else:
            self.vault_host = "https://" + settings.DOMAIN_NAME + "/" + self.space_code + "/vault"

        self.auth_token = None
        try:
            vault_token = VaultRecord.objects.get(user_code="hashicorp-vault-token")
            self.auth_token = json.loads(vault_token.data)["token"]
        except Exception as e:
            _l.info(f"Failed to get vault token: {e}")

    def get_headers(self):
        headers = {"X-Vault-Token": self.auth_token}

        return headers

    #  GENERAL ACTIONS STARTS

    def get_health(self):
        url = f"{self.vault_host}/v1/sys/health"  # warning should be no trailing slash
        headers = self.get_headers()

        try:
            response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info("Vault get health successfully")
        except Exception as e:
            _l.info(f"Failed to get health: {e}")

        return response.json()

    def get_status(self):
        url = f"{self.vault_host}/v1/sys/seal-status"  # warning should be no trailing slash
        headers = self.get_headers()

        try:
            response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info("Vault get status successfully")
        except Exception as e:
            _l.info(f"Failed to get status: {e}")

        return response.json()

    def init(self):
        url = f"{self.vault_host}/v1/sys/init"  # warning should be no trailing slash
        headers = self.get_headers()

        data = {"secret_shares": 5, "secret_threshold": 3}

        try:
            response = requests.post(url, json=data, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info("Vault inited successfully")
        except Exception as e:
            _l.info(f"Failed to init: {e}")

        return response.json()

    def seal(self):
        url = f"{self.vault_host}/v1/sys/seal"  # warning should be no trailing slash
        headers = self.get_headers()

        try:
            response = requests.post(url, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info("Vault sealed successfully")
        except Exception as e:
            _l.info(f"Failed to seal: {e}")

    def unseal(self, key):
        url = f"{self.vault_host}/v1/sys/unseal"  # warning should be no trailing slash
        headers = self.get_headers()

        data = {"key": key}

        try:
            response = requests.post(url, json=data, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info("Vault sealed successfully")
        except Exception as e:
            _l.info(f"Failed to seal: {e}")

    # GENERAL ACTIONS ENDS

    def get_list_engines(
        self,
    ):
        url = f"{self.vault_host}/v1/sys/mounts"
        headers = self.get_headers()
        response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)

        response_json = response.json()

        filtered_list = []

        if "data" in response_json:
            formatted_data = remove_trailing_slash_from_keys(response_json["data"])

            filtered_keys = ["sys", "identity", "cubbyhole"]

            filtered_list = [
                {"engine_name": k, "data": v} for k, v in formatted_data.items() if k not in filtered_keys
            ]

        return filtered_list

    def create_engine(self, engine_name):
        url = f"{self.vault_host}/v1/sys/mounts/{engine_name}"
        headers = self.get_headers()

        payload = {
            "path": engine_name,
            "type": "kv",
            "generate_signing_key": True,
            "config": {"id": engine_name},
            "options": {"version": 2},
        }

        try:
            response = requests.post(url, json=payload, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info(f"Secret engine {engine_name} created successfully")
        except Exception as e:
            _l.info(f"Failed to create secret engine: {e}")

        # return response.json()

    def delete_engine(self, engine_name):
        url = f"{self.vault_host}/v1/sys/mounts/{engine_name}"
        headers = self.get_headers()
        try:
            response = requests.delete(url, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info(f"Secret engine {engine_name} deleted successfully")
        except Exception as e:
            _l.info(f"Failed to delete secret engine: {e}")

    def get_list_secrets(self, engine_name):
        url = f"{self.vault_host}/v1/{engine_name}/metadata/?list=true"
        headers = self.get_headers()
        response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)
        return response.json()

    def create_secret(self, engine_name, secret_path, secret_data):
        url = f"{self.vault_host}/v1/{engine_name}/data/{secret_path}"
        headers = self.get_headers()

        data = {"data": secret_data, "options": {"cas": 0}}

        try:
            response = requests.post(url, headers=headers, json=data, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info(f"Secret {secret_path} created successfully")
        except Exception as e:
            _l.info(f"Failed to create secret: {e}")
        # return response.json()

    def get_secret_metadata(self, engine_name, secret_path):
        url = f"{self.vault_host}/v1/{engine_name}/metadata/{secret_path}"
        headers = self.get_headers()
        response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)
        return response.json()

    def get_latest_version(self, engine_name, secret_path):
        metadata = self.get_secret_metadata(engine_name, secret_path)

        version = len(metadata["data"]["versions"])

        return version

    def get_secret(self, engine_name, secret_path, version=1):
        url = f"{self.vault_host}/v1/{engine_name}/data/{secret_path}?version={version}"
        headers = self.get_headers()
        response = requests.get(url, headers=headers, verify=settings.VERIFY_SSL)
        return response.json()

    def update_secret(self, engine_name, secret_path, secret_data, version):
        url = f"{self.vault_host}/v1/{engine_name}/data/{secret_path}"
        headers = self.get_headers()

        data = {"data": secret_data, "options": {"cas": version}}

        try:
            response = requests.put(url, headers=headers, json=data, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info(f"Secret {secret_path} updated successfully")
        except Exception as e:
            _l.info(f"Failed to update secret: {e}")

    def delete_secret(self, engine_name, secret_path):
        url = f"{self.vault_host}/v1/{engine_name}/metadata/{secret_path}"
        headers = self.get_headers()

        try:
            response = requests.delete(url, headers=headers, verify=settings.VERIFY_SSL)
            response.raise_for_status()
            _l.info(f"Secret {secret_path} deleted successfully")
        except Exception as e:
            _l.info(f"Failed to delete secret: {e}")
