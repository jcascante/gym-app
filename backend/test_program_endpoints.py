#!/usr/bin/env python3
"""
Test script for program builder endpoints.
"""
import requests
import json


def test_program_endpoints():
    """Test the program creation endpoints end-to-end."""

    base_url = "http://localhost:8000/api/v1"

    print("=" * 60)
    print("Testing Program Builder Endpoints")
    print("=" * 60)

    # Step 1: Login
    print("\n1. Logging in as admin@testgym.com...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        data={
            "username": "admin@testgym.com",
            "password": "Admin123!"
        }
    )

    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return

    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"✅ Login successful! Token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Get calculation constants
    print("\n2. Fetching calculation constants...")
    constants_response = requests.get(
        f"{base_url}/programs/algorithms/strength_linear_5x5/constants",
        headers=headers
    )

    if constants_response.status_code != 200:
        print(f"❌ Failed to get constants: {constants_response.status_code}")
        print(constants_response.text)
        return

    constants = constants_response.json()
    print(f"✅ Got constants version: {constants['version']}")
    print(f"   Weekly jump table: {len(constants['weekly_jump_table'])} entries")
    print(f"   Ramp up table: {len(constants['ramp_up_table'])} entries")

    # Step 3: Preview program
    print("\n3. Generating program preview...")
    preview_input = {
        "builder_type": "strength_linear_5x5",
        "name": "Test Strength Program",
        "description": "Testing the program builder",
        "movements": [
            {
                "name": "Squat",
                "one_rm": 315,
                "max_reps_at_80_percent": 12,
                "target_weight": 275
            },
            {
                "name": "Bench Press",
                "one_rm": 225,
                "max_reps_at_80_percent": 10,
                "target_weight": 185
            }
        ],
        "duration_weeks": 8,
        "days_per_week": 4,
        "is_template": True
    }

    preview_response = requests.post(
        f"{base_url}/programs/preview",
        headers=headers,
        json=preview_input
    )

    if preview_response.status_code != 200:
        print(f"❌ Preview failed: {preview_response.status_code}")
        print(preview_response.text)
        return

    preview = preview_response.json()
    print(f"✅ Preview generated!")
    print(f"   Algorithm version: {preview['algorithm_version']}")
    print(f"   Weeks: {len(preview['weeks'])}")
    print(f"   Calculated data:")
    for movement, calc in preview['calculated_data'].items():
        print(f"     {movement}:")
        print(f"       Weekly jump: {calc['weekly_jump_percent']}% ({calc['weekly_jump_lbs']} lbs)")
        print(f"       Ramp up: {calc['ramp_up_percent']}% ({calc['ramp_up_base_lbs']} lbs)")

    # Step 4: Save program
    print("\n4. Saving program to database...")
    save_response = requests.post(
        f"{base_url}/programs",
        headers=headers,
        json=preview_input
    )

    if save_response.status_code != 201:
        print(f"❌ Save failed: {save_response.status_code}")
        print(save_response.text)
        return

    saved_program = save_response.json()
    print(f"✅ Program saved successfully!")
    print(f"   ID: {saved_program['id']}")
    print(f"   Name: {saved_program['name']}")
    print(f"   Builder type: {saved_program['builder_type']}")
    print(f"   Duration: {saved_program['duration_weeks']} weeks")
    print(f"   Days per week: {saved_program['days_per_week']}")
    print(f"   Is template: {saved_program['is_template']}")

    print("\n" + "=" * 60)
    print("✅ All tests passed! Program builder is fully functional.")
    print("=" * 60)


if __name__ == "__main__":
    test_program_endpoints()
