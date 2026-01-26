import requests
import uuid

BASE_URL = "http://localhost:8002"
DEFAULT_TENANT = "default-tenant-0000"

def test_catalog():
    # 1. Test Default Tenant (Header Missing -> defaults to default-tenant-0000)
    print(f"\n[TEST] Listing Restaurants (Default Tenant)...")
    res = requests.get(f"{BASE_URL}/catalog/restaurants")
    if res.status_code == 200:
        data = res.json()
        print(f"✅ Found {len(data)} restaurants.")
        if len(data) > 0:
            r_id = data[0]["id"]
            print(f"   - First: {data[0]['name']} (ID: {r_id})")
            
            # 2. Get Menus for this restaurant
            print(f"[TEST] Getting Menus for {r_id}...")
            m_res = requests.get(f"{BASE_URL}/catalog/restaurants/{r_id}/menus")
            if m_res.status_code == 200:
                menus = m_res.json()
                print(f"✅ Found {len(menus)} menus.")
                if len(menus) > 0:
                    m_id = menus[0]["id"]
                    # 3. Get Items (using our extra endpoint)
                    print(f"[TEST] Getting Items for Menu {m_id}...")
                    i_res = requests.get(f"{BASE_URL}/catalog/menus/{m_id}/items")
                    if i_res.status_code == 200:
                        items = i_res.json()
                        print(f"✅ Found {len(items)} items.")
                    else:
                         print(f"❌ Failed to get items: {i_res.text}")
            else:
                print(f"❌ Failed to get menus: {m_res.text}")
    else:
        print(f"❌ Failed to list restaurants: {res.text}")

    # 4. Test Events
    print(f"\n[TEST] Listing Events...")
    e_res = requests.get(f"{BASE_URL}/catalog/events")
    if e_res.status_code == 200:
        events = e_res.json()
        print(f"✅ Found {len(events)} events.")
    else:
        print(f"❌ Failed to list events: {e_res.text}")

    # 5. Test Isolation (Random Tenant)
    rando = str(uuid.uuid4())
    print(f"\n[TEST] Listing Restaurants for Random Tenant ({rando})...")
    res_iso = requests.get(f"{BASE_URL}/catalog/restaurants", headers={"X-Tenant-ID": rando})
    if res_iso.status_code == 200:
        data_iso = res_iso.json()
        if len(data_iso) == 0:
            print(f"✅ Correctly empty for unknown tenant.")
        else:
            print(f"❌ Isolation Fail: Found data for random tenant?!")
    else:
        print(f"❌ Request failed: {res_iso.text}")

if __name__ == "__main__":
    try:
        test_catalog()
    except Exception as e:
        print(f"Test crashed: {e}")
