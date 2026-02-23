#!/usr/bin/env python3
"""
Simple end-to-end script to verify program assignment and client `/me/programs`.

Requires a running dev server at http://localhost:8000/api/v1
"""
import requests
import uuid
import time

BASE = "http://localhost:8000/api/v1"


def test_client_program_flow():
    print("Logging in as admin@testgym.com...")
    login = requests.post(f"{BASE}/auth/login", data={"username": "admin@testgym.com", "password": "Admin123!"})
    if login.status_code != 200:
        print("Login failed, ensure dev server is running and seed data exists.")
        print(login.status_code, login.text)
        return

    token = login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create a new client user with known password
    client_email = f"test_client_{int(time.time())}@example.com"
    client_payload = {
        "email": client_email,
        "password": "Client123!",
        "role": "CLIENT",
    }

    print(f"Creating client {client_email}...")
    create_resp = requests.post(f"{BASE}/users", json=client_payload, headers=headers)
    if create_resp.status_code not in (200, 201):
        print("Failed to create client:", create_resp.status_code, create_resp.text)
        return

    client = create_resp.json()
    client_id = client.get("id")
    print("Client created, id=", client_id)

    # Create a simple program via POST /programs (reuse preview inputs)
    preview_input = {
        "builder_type": "strength_linear_5x5",
        "name": "E2E Test Program",
        "description": "Auto-created test program",
        "movements": [
            {"name": "Squat", "one_rm": 200, "max_reps_at_80_percent": 10, "target_weight": 180},
        ],
        "duration_weeks": 4,
        "days_per_week": 3,
        "is_template": True
    }

    print("Creating program template...")
    prog_resp = requests.post(f"{BASE}/programs", json=preview_input, headers=headers)
    if prog_resp.status_code != 201:
        print("Failed to create program:", prog_resp.status_code, prog_resp.text)
        return

    program = prog_resp.json()
    program_id = program.get("id")
    print("Program created id=", program_id)

    # Assign program to client
    assign_payload = {"client_id": client_id, "assignment_name": "E2E Assign", "notes": "Test assign"}
    print("Assigning program to client...")
    assign_resp = requests.post(f"{BASE}/programs/{program_id}/assign", json=assign_payload, headers=headers)
    if assign_resp.status_code != 201:
        print("Failed to assign program:", assign_resp.status_code, assign_resp.text)
        return

    assignment = assign_resp.json()
    print("Assigned:", assignment)

    # Login as client and call /me/programs
    print("Logging in as client to verify /me/programs...")
    client_login = requests.post(f"{BASE}/auth/login", data={"username": client_email, "password": "Client123!"})
    if client_login.status_code != 200:
        print("Client login failed:", client_login.status_code, client_login.text)
        return

    client_token = client_login.json().get("access_token")
    client_headers = {"Authorization": f"Bearer {client_token}"}

    me_prog = requests.get(f"{BASE}/me/programs", headers=client_headers)
    print("/me/programs status:", me_prog.status_code)
    try:
        print(me_prog.json())
    except Exception:
        print(me_prog.text)


if __name__ == '__main__':
    test_client_program_flow()
