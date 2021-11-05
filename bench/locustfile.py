from locust import HttpUser, between, task
import base64

class WebsiteUser(HttpUser):
    wait_time = between(1, 10)

    USERNAME = "nats"
    PASSWORD = "test"
    BASIC_AUTH = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode("ascii"))

    TOKEN = "test"

    JWT = ""

    NKEY = "SUADNX5WHATOIHYBJBLSHWBMQXIS4TTQKOMBSTCGZL43GCGVLZYETSPVK4"

    @task
    def anonymous(self):
        self.client.get("/test")

    @task
    def basic_auth(self):

        self.client.get("/test", headers={f"Authorization: Basic {self.BASIC_AUTH}"})

    @task
    def bearer_auth(self):

        self.client.get("/test", headers={f"Authorization: Bearer {self.TOKEN}"})

    @task
    def jwt_token_auth(self):

        self.client.get("/test", headers={f"Authorization: Bearer {self.JWT}"})

    @task
    def nkeys_auth(self):
        self.client.get(
            "/test",
            headers={
                "X-NKEYS-SEED": self.NKEY,
            }
        )
