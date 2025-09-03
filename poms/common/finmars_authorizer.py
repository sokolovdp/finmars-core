import datetime
import json
from logging import getLogger

import jwt
import requests
from rest_framework_simplejwt.tokens import RefreshToken

from poms_app import settings

_l = getLogger("poms.authorizer")


class AuthorizerService:
    # ?space_code=... needs for JWT Auth purpose !!!

    @staticmethod
    def create_jwt_token():
        payload = {
            "some": "payload",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),  # Expires in 1 day
        }
        secret_key = settings.SECRET_KEY
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    @staticmethod
    def prepare_refresh_token() -> RefreshToken:
        # User = get_user_model()
        #
        # # Probably need to come up with something more smart
        # bot = User.objects.get(username="finmars_bot")
        #
        # return RefreshToken.for_user(bot)

        return AuthorizerService.create_jwt_token()

    def prepare_headers(self) -> dict:
        token = self.prepare_refresh_token()
        return {
            "Content-type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def invite_member(self, member, from_user, realm_code, space_code):
        headers = self.prepare_headers()
        data = {
            "realm_code": realm_code,
            "space_code": space_code,
            "base_api_url": space_code,  # deprecated, delete, but be sure authorizer not using it
            "username": member.username,
            "is_admin": member.is_admin,
            "from_user_username": from_user.username,
        }
        url = f"{settings.AUTHORIZER_URL}/api/v1/internal/invite-member/?space_code={space_code}"

        _l.info(f"invite_member url={url} data={data}")

        response = requests.post(url=url, data=json.dumps(data), headers=headers, verify=settings.VERIFY_SSL)
        if response.status_code != 200:
            raise RuntimeError(
                f"Authorizer API error, data={data} code={response.status_code} details={response.text}"
            )

    def kick_member(self, member, realm_code, space_code):
        headers = self.prepare_headers()
        data = {
            "realm_code": realm_code,
            "space_code": space_code,
            "base_api_url": space_code,  # deprecated, but, be sure that authorizer not using it
            "username": member.username,
        }
        url = f"{settings.AUTHORIZER_URL}/api/v1/internal/kick-member/?space_code={space_code}"

        _l.info(f"kick_member url={url} data={data}")

        response = requests.post(url=url, data=json.dumps(data), headers=headers, verify=settings.VERIFY_SSL)
        if response.status_code != 200:
            raise RuntimeError(f"Error kicking member {response.text}")

    def update_member(self, member, realm_code, space_code, **kwargs):
        headers = self.prepare_headers()
        data = {
            "realm_code": realm_code,
            "space_code": space_code,
            "username": member.username,
        }
        data.update(**kwargs)
        url = f"{settings.AUTHORIZER_URL}/api/v2/internal/update-member/"

        _l.info(f"update_member url={url} data={data}")

        response = requests.post(url=url, data=json.dumps(data), headers=headers, verify=settings.VERIFY_SSL)
        if response.status_code != 200:
            raise RuntimeError(f"Error updating member {response.text}")

    def prepare_and_post_request(self, url, worker, realm_code, err_msg):
        headers = self.prepare_headers()
        data = {
            "realm_code": realm_code,
            "worker_name": worker.worker_name,
        }
        url = f"{settings.AUTHORIZER_URL}{url}"
        response = requests.post(
            url=url,
            data=json.dumps(data),
            headers=headers,
            verify=settings.VERIFY_SSL,
        )
        if response.status_code != 200:
            raise RuntimeError(f"{err_msg}{response.text}")

    def start_worker(self, worker, realm_code):
        self.prepare_and_post_request(
            "/api/v1/internal/start-worker/",
            worker,
            realm_code,
            "Error starting worker ",
        )

    def stop_worker(self, worker, realm_code):
        self.prepare_and_post_request(
            "/api/v1/internal/stop-worker/",
            worker,
            realm_code,
            "Error stopping worker ",
        )

    def restart_worker(self, worker, realm_code):
        self.prepare_and_post_request(
            "/api/v1/internal/restart-worker/",
            worker,
            realm_code,
            "Error restarting worker ",
        )

    def delete_worker(self, worker, realm_code):
        self.prepare_and_post_request(
            "/api/v1/internal/delete-worker/",
            worker,
            realm_code,
            "Error deleting worker ",
        )

    def get_worker_status(self, worker, realm_code):
        headers = self.prepare_headers()
        url = (
            f"{settings.AUTHORIZER_URL}/api/v1/internal/worker-status/"
            f"?realm_code={realm_code}&worker_name={worker.worker_name}"
        )

        response = requests.get(url=url, headers=headers, verify=settings.VERIFY_SSL)
        if response.status_code != 200:
            raise RuntimeError(f"Error getting worker status {response.text}")

        return response.json()

    def create_worker(self, worker, realm_code):
        headers = self.prepare_headers()
        data = {
            "realm_code": realm_code,
            "worker_name": worker.worker_name,
            "worker_type": worker.worker_type,
            "memory_limit": worker.memory_limit,
            "queue": worker.queue,
        }
        url = f"{settings.AUTHORIZER_URL}/api/v1/internal/create-worker/"

        response = requests.post(url=url, data=json.dumps(data), headers=headers, verify=settings.VERIFY_SSL)
        if response.status_code != 200:
            raise RuntimeError(f"Error creating worker {response.text}")
