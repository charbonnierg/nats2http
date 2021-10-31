from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(1, 10)
    
    @task
    def index(self):
        response = self.client.get("/test")
        assert response.status_code == 200

