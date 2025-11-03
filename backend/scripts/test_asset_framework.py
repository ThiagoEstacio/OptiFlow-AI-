#!/usr/bin/env python3
"""
Automated testing script for Asset Framework
Tests API endpoints, calculated attributes, and health scores
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from typing import Dict, Any, Optional

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TIMEOUT = 10.0

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class AssetFrameworkTester:
    """Automated tester for Asset Framework"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.test_asset_id: Optional[str] = None
        self.test_attribute_id: Optional[str] = None

        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0

    async def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}🧪 Asset Framework Automated Tests{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        # Test categories
        await self.test_asset_endpoints()
        await self.test_attribute_endpoints()
        await self.test_calculated_attributes()
        await self.test_health_score()

        # Summary
        self.print_summary()

    async def test_asset_endpoints(self):
        """Test Asset CRUD endpoints"""
        print(f"\n{YELLOW}📦 Testing Asset Endpoints...{RESET}\n")

        # 1. List assets
        await self.test(
            "GET /assets/ - List all assets",
            lambda: self.client.get(f"{self.base_url}/assets/"),
            lambda r: len(r.json()) > 0
        )

        # 2. Get asset tree
        await self.test(
            "GET /assets/tree - Get asset tree",
            lambda: self.client.get(f"{self.base_url}/assets/tree"),
            lambda r: isinstance(r.json(), list)
        )

        # 3. Create asset
        create_data = {
            "name": "Test Asset Automated",
            "description": "Created by automated test",
            "asset_type": "equipment",
            "metadata": {"test": "true"}
        }

        async def create_and_store():
            response = await self.client.post(f"{self.base_url}/assets/", json=create_data)
            if response.status_code == 201:
                self.test_asset_id = response.json()["id"]
            return response

        await self.test(
            "POST /assets/ - Create asset",
            create_and_store,
            lambda r: r.status_code == 201 and "id" in r.json()
        )

        # 4. Get specific asset
        if self.test_asset_id:
            await self.test(
                f"GET /assets/{{id}} - Get asset details",
                lambda: self.client.get(f"{self.base_url}/assets/{self.test_asset_id}"),
                lambda r: r.json()["name"] == "Test Asset Automated"
            )

            # 5. Update asset
            update_data = {"name": "Test Asset Updated"}
            await self.test(
                "PUT /assets/{{id}} - Update asset",
                lambda: self.client.put(f"{self.base_url}/assets/{self.test_asset_id}", json=update_data),
                lambda r: r.json()["name"] == "Test Asset Updated"
            )

    async def test_attribute_endpoints(self):
        """Test Attribute CRUD endpoints"""
        print(f"\n{YELLOW}🏷️  Testing Attribute Endpoints...{RESET}\n")

        if not self.test_asset_id:
            print(f"{YELLOW}⚠️  Skipping attribute tests (no test asset){RESET}")
            return

        # 1. Create static attribute
        attr_data = {
            "asset_id": self.test_asset_id,
            "name": "Test Static Attribute",
            "description": "Static test attribute",
            "attribute_type": "static",
            "static_value": "100",
            "unit": "kg",
            "display_order": 0,
            "settings": {"min": 0, "max": 200}
        }

        async def create_attribute():
            response = await self.client.post(
                f"{self.base_url}/assets/{self.test_asset_id}/attributes",
                json=attr_data
            )
            if response.status_code == 201:
                self.test_attribute_id = response.json()["id"]
            return response

        await self.test(
            "POST /assets/{{id}}/attributes - Create attribute",
            create_attribute,
            lambda r: r.status_code == 201
        )

        # 2. List attributes
        await self.test(
            "GET /assets/{{id}}/attributes - List attributes",
            lambda: self.client.get(f"{self.base_url}/assets/{self.test_asset_id}/attributes"),
            lambda r: len(r.json()) > 0
        )

    async def test_calculated_attributes(self):
        """Test Calculated Attributes engine"""
        print(f"\n{YELLOW}🧮 Testing Calculated Attributes...{RESET}\n")

        if not self.test_asset_id:
            print(f"{YELLOW}⚠️  Skipping calculated tests (no test asset){RESET}")
            return

        # 1. Simple math
        await self.test(
            "Evaluate formula: 2 + 2",
            lambda: self.client.post(
                f"{self.base_url}/assets/evaluate-formula",
                params={"formula": "2 + 2", "asset_id": self.test_asset_id}
            ),
            lambda r: r.json()["result"] == 4.0 and r.json()["success"]
        )

        # 2. Math functions
        await self.test(
            "Evaluate formula: sqrt(16)",
            lambda: self.client.post(
                f"{self.base_url}/assets/evaluate-formula",
                params={"formula": "sqrt(16)", "asset_id": self.test_asset_id}
            ),
            lambda r: r.json()["result"] == 4.0
        )

        # 3. Complex expression
        await self.test(
            "Evaluate formula: (10 * 2) / 5 + 3",
            lambda: self.client.post(
                f"{self.base_url}/assets/evaluate-formula",
                params={"formula": "(10 * 2) / 5 + 3", "asset_id": self.test_asset_id}
            ),
            lambda r: r.json()["result"] == 7.0
        )

        # 4. Attribute reference
        await self.test(
            "Evaluate formula: attr('Test Static Attribute')",
            lambda: self.client.post(
                f"{self.base_url}/assets/evaluate-formula",
                params={"formula": "attr('Test Static Attribute')", "asset_id": self.test_asset_id}
            ),
            lambda r: r.json()["result"] == 100.0
        )

        # 5. Invalid formula (should handle gracefully)
        await self.test(
            "Invalid formula handling",
            lambda: self.client.post(
                f"{self.base_url}/assets/evaluate-formula",
                params={"formula": "invalid()", "asset_id": self.test_asset_id}
            ),
            lambda r: not r.json()["success"]
        )

    async def test_health_score(self):
        """Test Health Score calculations"""
        print(f"\n{YELLOW}💚 Testing Health Score...{RESET}\n")

        if not self.test_asset_id:
            print(f"{YELLOW}⚠️  Skipping health tests (no test asset){RESET}")
            return

        # 1. Get asset health
        await self.test(
            "GET /assets/{{id}}/health - Get health score",
            lambda: self.client.get(f"{self.base_url}/assets/{self.test_asset_id}/health"),
            lambda r: "health_score" in r.json() and "status" in r.json()
        )

        # 2. Health overview
        await self.test(
            "GET /assets/health/overview - Get overview",
            lambda: self.client.get(f"{self.base_url}/assets/health/overview"),
            lambda r: "total_assets" in r.json() and "average_health_score" in r.json()
        )

    async def test(self, name: str, request_func, validate_func):
        """Run a single test"""
        self.tests_run += 1

        try:
            response = await request_func()

            if validate_func(response):
                print(f"{GREEN}✓{RESET} {name}")
                self.tests_passed += 1
            else:
                print(f"{RED}✗{RESET} {name}")
                print(f"  {RED}Response: {response.json()}{RESET}")
                self.tests_failed += 1

        except Exception as e:
            print(f"{RED}✗{RESET} {name}")
            print(f"  {RED}Error: {str(e)}{RESET}")
            self.tests_failed += 1

    async def cleanup(self):
        """Clean up test data"""
        print(f"\n{YELLOW}🧹 Cleaning up test data...{RESET}")

        # Delete test asset (cascades to attributes)
        if self.test_asset_id:
            try:
                await self.client.delete(f"{self.base_url}/assets/{self.test_asset_id}")
                print(f"{GREEN}✓{RESET} Test asset deleted")
            except Exception as e:
                print(f"{YELLOW}⚠️  Could not delete test asset: {e}{RESET}")

        await self.client.aclose()

    def print_summary(self):
        """Print test summary"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}📊 Test Summary{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        print(f"Total Tests: {self.tests_run}")
        print(f"{GREEN}Passed: {self.tests_passed}{RESET}")
        print(f"{RED}Failed: {self.tests_failed}{RESET}")

        if self.tests_failed == 0:
            print(f"\n{GREEN}🎉 All tests passed!{RESET}")
            success_rate = 100
        else:
            success_rate = (self.tests_passed / self.tests_run) * 100
            print(f"\n{YELLOW}⚠️  Some tests failed{RESET}")

        print(f"Success Rate: {success_rate:.1f}%\n")


async def main():
    """Main test runner"""
    tester = AssetFrameworkTester()

    try:
        await tester.run_all_tests()
    finally:
        await tester.cleanup()

    # Exit with error code if tests failed
    sys.exit(0 if tester.tests_failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
