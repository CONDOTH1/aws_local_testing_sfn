import os
import time
import requests


def wait_for_service(service_name: str):
    try:
        res = requests.get(f"http://{service_name.lower()}:5000/health")
        res.raise_for_status()
        print(f"{service_name} is now available.")
    except Exception as e:
        print(e)
        time.sleep(1)
        wait_for_service(service_name=service_name)


if __name__ == "__main__":
    waiting_for = os.getenv('WAITING_FOR')
    wait_for_service(waiting_for)