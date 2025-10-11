"""
Helper script to add time extraction assertions to test cases.
"""

# Time assertions to add to each test case:
# Format: test_method_name: (year, month, day, hour, minute, second)

time_assertions = {
    # ABA Bank
    "test_aba_english_khr": (2025, 10, 11, 10, 21, None),  # "Oct 11, 10:21 AM"
    "test_aba_english_usd": (2025, 10, 11, 10, 21, None),  # "Oct 11, 10:21 AM"

    # PLB Bank
    "test_plb_khr": (2025, 10, 11, 10, 8, 57),  # "2025-10-11 10:08:57"
    "test_plb_usd": (2025, 10, 11, 9, 36, 33),  # "2025-10-11 09:36:33"

    # Canadia Bank
    "test_canadia_usd": (2025, 10, 11, 10, 8, 53),  # "11 OCT 2025 at 10:08:53"

    # HLB Bank
    "test_hlb_khr": (2025, 10, 11, 10, 23, 23),  # "11-Oct-2025 @10:23:23"
    "test_hlb_usd": (2025, 10, 9, 16, 0, 50),  # "09-Oct-2025 @16:00:50"

    # Vattanac Bank
    "test_vattanac_usd": (2025, 10, 4, 21, 32, None),  # "04/10/2025 09:32 PM"
    "test_vattanac_khr": (2025, 10, 5, 19, 52, None),  # "05/10/2025 07:52 PM"

    # CP Bank
    "test_cpbank_khr_received": (2025, 10, 11, 10, 52, 51),  # "11-10-2025 10:52:51 AM"
    "test_cpbank_khr_amount": (2025, 9, 29, 18, 15, 56),  # "29-09-2025 06:15:56 PM"
    "test_cpbank_usd_received": (2025, 10, 11, 8, 27, 3),  # "11-10-2025 08:27:03 AM"
    "test_cpbank_usd_amount": (2025, 10, 9, 13, 11, 55),  # "09-10-2025 01:11:55 PM"

    # Sathapana Bank
    "test_sathapana_usd": (2025, 10, 4, 8, 58, 45),  # "2025-10-04 08.58.45 AM"
    "test_sathapana_khr": (2025, 10, 9, 7, 58, 21),  # "2025-10-09 07.58.21 AM"

    # Chip Mong Bank
    "test_chipmong_khr": (2025, 10, 11, 11, 28, None),  # "Oct 11, 2025 11:28 AM"
    "test_chipmong_usd": (2025, 10, 10, 20, 0, None),  # "Oct 10, 2025 08:00 PM"

    # PRASAC Bank
    "test_prasac_usd": (2025, 10, 11, 9, 43, 44),  # "11-Oct-25 09:43.44 AM"
    "test_prasac_khr": (2025, 10, 11, 10, 12, 41),  # "11-Oct-25 10:12.41 AM"

    # AMK Bank
    "test_amk_khr": (2025, 9, 15, 16, 17, None),  # "15-09-2025 04:17 PM"

    # Prince Bank
    "test_prince_usd": (2025, 9, 26, 22, 7, None),  # "2025/09/26, 10:07 pm"
    "test_prince_khr": (2025, 10, 10, 22, 36, None),  # "2025/10/10, 10:36 pm"

    # S7POS
    "test_s7pos_khmer_format": (2025, 10, 11, 10, 58, 0),  # "2025-10-11 10:58:00"
}


# Code template for time assertions
def generate_assertion(year, month, day, hour, minute, second):
    assertions = [
        "        self.assertIsNotNone(trx_time)",
        f"        self.assertEqual(trx_time.year, {year})",
        f"        self.assertEqual(trx_time.month, {month})",
        f"        self.assertEqual(trx_time.day, {day})",
        f"        self.assertEqual(trx_time.hour, {hour})",
        f"        self.assertEqual(trx_time.minute, {minute})",
    ]

    if second is not None:
        assertions.append(f"        self.assertEqual(trx_time.second, {second})")

    return "\n".join(assertions)


if __name__ == "__main__":
    print("Time assertions to add to each test:")
    print("=" * 60)

    for test_name, time_values in time_assertions.items():
        year, month, day, hour, minute, second = time_values
        print(f"\n{test_name}:")
        print(generate_assertion(year, month, day, hour, minute, second))
        print()
