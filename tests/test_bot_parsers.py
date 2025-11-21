"""
Unit tests for bot-specific message parsers.

This test file validates the optimized parser implementations for all 15 supported bots.
Each test case uses real message samples from the production environment.
"""

import unittest

from helper.message_parser_optimized import extract_amount_currency_and_time


class TestACLEDABankParser(unittest.TestCase):
    """Tests for ACLEDABankBot parser (parse_acleda)"""

    def test_acleda_khmer_usd(self):
        """Test ACLEDA Khmer USD message"""
        message = "បានទទួល 21.15 ដុល្លារ ពី 097 8555 757 Saing Sopheak, ថ្ងៃទី១១ តុលា ២០២៥ ១០:១៩ព្រឹក, លេខយោង 52841751197, នៅ PHE MUYTOUNG."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "ACLEDABankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 21.15)
        # Note: Time extraction for Khmer dates not yet implemented

    def test_acleda_khmer_khr(self):
        """Test ACLEDA Khmer KHR message"""
        message = "បានទទួល 17,000 រៀល ពី 088 9154 199 Hun Sok Han, ថ្ងៃទី១១ តុលា ២០២៥ ១០:១៩ព្រឹក, លេខយោង 52841750404, នៅ PHE MUYTOUNG."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"ACLEDABankBot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 17000)

    def test_acleda_english_usd(self):
        """Test ACLEDA English USD message"""
        message = "Received 9.60 USD from 089 536 367 Tot sochea, 11-Oct-2025 10:12AM. Ref.ID: 52841705680, at CALTEX  APOLLO 926 I, STAND: 05843451."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"ACLEDABankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 9.60)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 12)

    def test_acleda_english_khr(self):
        """Test ACLEDA English KHR message"""
        message = "Received 5,000 KHR from 097 9841 404 PO LYHOR, 11-Oct-2025 10:13AM. Ref.ID: 52841706944, at Yellow Mart Norton, STAND: 0000011034."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"ACLEDABankBot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 5000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 13)


class TestABABankParser(unittest.TestCase):
    """Tests for PayWayByABA_bot parser (parse_aba)"""

    def test_aba_english_khr(self):
        """Test ABA English KHR message"""
        message = "៛78,000 paid by CHOR SEIHA (*655) on Oct 11, 10:21 AM via ABA PAY at KEAM LILAY. Trx. ID: 176015291441643, APV: 134672."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PayWayByABA_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 78000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 21)
        self.assertEqual(paid_by, '655')

    def test_aba_english_usd(self):
        """Test ABA English USD message"""
        message = "$10.00 paid by LOR PISETH (*467) on Oct 11, 10:21 AM via ABA PAY at KEAM LILAY. Trx. ID: 176015291049703, APV: 691804."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PayWayByABA_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 21)
        self.assertEqual(paid_by, '467')

    def test_aba_khmer_khr(self):
        """Test ABA Khmer KHR message"""
        message = "៛10,400 ត្រូវបានបង់ដោយ Eang Sreyneang (*111) នៅថ្ងៃទី 11 ខែតុលា ឆ្នាំ 2025 ម៉ោង 10:15 តាម ABA KHQR (ACLEDA Bank Plc.) នៅ KiLiYaSation by P.KET។ លេខប្រតិបត្តិការ: 176015253655195។ APV: 165582។"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PayWayByABA_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 10400)
        self.assertEqual(paid_by, '111')

    def test_aba_khmer_usd(self):
        """Test ABA Khmer USD message"""
        message = "$4.00 ត្រូវបានបង់ដោយ NANG NALIN (*775) នៅថ្ងៃទី 11 ខែតុលា ឆ្នាំ 2025 ម៉ោង 10:10 តាម ABA KHQR (ACLEDA Bank Plc.) នៅ PHY SREYNANG។ លេខប្រតិបត្តិការ: 176015224834254។ APV: 943476។"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PayWayByABA_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 4.00)
        self.assertEqual(paid_by, '775')


class TestCCUBankParser(unittest.TestCase):
    """Tests for CCU Bank parser (parse_ccu)"""

    def test_ccu_usd_paid_by(self):
        """Test CCU Bank USD 'paid by' format with Hash ID"""
        message = "105.00 USD is paid by SOYANUK SAMOEURN, ABA Bank *3961 on 31-October-2025, 08:35PM at X Gear Computer with Hash ID #865ecfef"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "ccu_bank_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 105.0)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 31)
        self.assertEqual(trx_time.hour, 20)
        self.assertEqual(trx_time.minute, 35)

    def test_ccu_khr_paid_by(self):
        """Test CCU Bank KHR 'paid by' format with Hash ID"""
        message = "5,000.00 KHR is paid by THAIYUTH SOPHEAP, ABA Bank *2505 on 31-October-2025, 08:18PM at X Gear Computer with Hash ID #a1e837e7"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "ccu_bank_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 5000.0)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 31)
        self.assertEqual(trx_time.hour, 20)
        self.assertEqual(trx_time.minute, 18)


class TestPLBBankParser(unittest.TestCase):
    """Tests for PLBITBot parser (parse_plb)"""

    def test_plb_khr(self):
        """Test PLB KHR message"""
        message = "4,000 KHR was credited by CHANRAINGSEY NORATH                                (ABA Bank) via KHQR to Mixue Mean Chey on 2025-10-11 10:08:57 Ref. No. 58489"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PLBITBot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 4000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 8)
        self.assertEqual(trx_time.second, 57)

    def test_plb_usd(self):
        """Test PLB USD message"""
        message = "2.65 USD was credited by VITOU SOKTHY                                       (ABA Bank) via KHQR to MIXUE TAKHMAO 2 on 2025-10-11 09:36:33 Ref. No. 46201"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"PLBITBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 2.65)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 9)
        self.assertEqual(trx_time.minute, 36)
        self.assertEqual(trx_time.second, 33)


class TestCanadiaBankParser(unittest.TestCase):
    """Tests for CanadiaMerchant_bot parser (parse_canadia)"""

    def test_canadia_usd(self):
        """Test Canadia USD message"""
        message = "1.50 USD was paid to your account: ZTO EXPRESS 1154039021 on 11 OCT 2025 at 10:08:53 from  Advanced Bank of Asia Ltd. Acc: THIDA NGUON 001XXXXXXXX5870 with Ref: FT25284T1CZ3, Txn Hash: f12176a6"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"CanadiaMerchant_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 1.50)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 8)
        self.assertEqual(trx_time.second, 53)


class TestHLBBankParser(unittest.TestCase):
    """Tests for HLBCAM_Bot parser (parse_hlb)"""

    def test_hlb_khr(self):
        """Test HLB KHR message"""
        message = "KHR 14,000.00 is paid to INFINITE MINI WASH from VANDALY LONG on 11-Oct-2025 @10:23:23. Transaction Hash is d6349c17."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"HLBCAM_Bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 14000.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 23)
        self.assertEqual(trx_time.second, 23)

    def test_hlb_usd(self):
        """Test HLB USD message"""
        message = "USD 5.00 is paid to INFINITE MINI WASH from ផេន សុកតិកា on 09-Oct-2025 @16:00:50. Transaction Hash is 37d263bf."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"HLBCAM_Bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 5.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 9)
        self.assertEqual(trx_time.hour, 16)
        self.assertEqual(trx_time.minute, 0)
        self.assertEqual(trx_time.second, 50)


class TestVattanacBankParser(unittest.TestCase):
    """Tests for vattanac_bank_merchant_prod_bot parser (parse_vattanac)"""

    def test_vattanac_usd(self):
        """Test Vattanac USD message"""
        message = """USD 16.50 is paid by VELAI SEUP (ABA Bank) via KHQR on 04/10/2025 09:32 PM at HOUSE 59 BY S.MEL
Trx. ID: 001FTRA252780212
Hash: 8babcc36"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"vattanac_bank_merchant_prod_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 16.50)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 4)
        self.assertEqual(trx_time.hour, 21)
        self.assertEqual(trx_time.minute, 32)

    def test_vattanac_khr(self):
        """Test Vattanac KHR message"""
        message = """KHR 16,500 is paid by NIPHA CHOULYNA (ACLEDA Bank Plc.) via KHQR on 05/10/2025 07:52 PM at NY STORE
Trx. ID: 001FTRA25278C54T
Hash: 68627074"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"vattanac_bank_merchant_prod_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 16500)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 5)
        self.assertEqual(trx_time.hour, 19)
        self.assertEqual(trx_time.minute, 52)


class TestCPBankParser(unittest.TestCase):
    """Tests for CPBankBot parser (parse_cpbank)"""

    def test_cpbank_khr_received(self):
        """Test CP Bank KHR received message"""
        message = "You have received KHR 104,000 from THANGMEAS KHIEV, bank name: ABA Bank ,account number: abaakhppxxx@abaa. Transaction Hash: 333986e5. Transaction Date: 11-10-2025 10:52:51 AM."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"CPBankBot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 104000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 52)
        self.assertEqual(trx_time.second, 51)

    def test_cpbank_khr_amount(self):
        """Test CP Bank KHR amount message"""
        message = "Transaction amount KHR 2,000 is paid from HUON SAONY to DARIYA RESTAURANT on 29-09-2025 06:15:56 PM. Transaction ID: CP2527208402"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"CPBankBot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 2000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 9)
        self.assertEqual(trx_time.day, 29)
        self.assertEqual(trx_time.hour, 18)
        self.assertEqual(trx_time.minute, 15)
        self.assertEqual(trx_time.second, 56)

    def test_cpbank_usd_received(self):
        """Test CP Bank USD received message"""
        message = "You have received USD 29.63 from SALY TOUR, bank name: ABA Bank ,account number: abaakhppxxx@abaa. Transaction Hash: 2727cf5c. Transaction Date: 11-10-2025 08:27:03 AM."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"CPBankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 29.63)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 8)
        self.assertEqual(trx_time.minute, 27)
        self.assertEqual(trx_time.second, 3)

    def test_cpbank_usd_amount(self):
        """Test CP Bank USD amount message"""
        message = "Transaction amount USD 5.50 is paid from CHIEV SAMITH to DARIYA RESTAURANT on 09-10-2025 01:11:55 PM. Transaction ID: CP2528205463"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"CPBankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 5.50)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 9)
        self.assertEqual(trx_time.hour, 13)
        self.assertEqual(trx_time.minute, 11)
        self.assertEqual(trx_time.second, 55)


class TestSathabanaBankParser(unittest.TestCase):
    """Tests for SathapanaBank_bot parser (parse_sathapana)"""

    def test_sathapana_usd(self):
        """Test Sathapana USD message"""
        message = "The amount 55.50 USD is paid from Khat Senghak, KB PRASAC Bank Plc, Bill No.: Payment breakfast | 02A64CSItFU on 2025-10-04 08.58.45 AM with Transaction ID: 099QORT252770056, Hash: 9277630f, Shop-name: Dariya Restaurant"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"SathapanaBank_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 55.50)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 4)
        self.assertEqual(trx_time.hour, 8)
        self.assertEqual(trx_time.minute, 58)
        self.assertEqual(trx_time.second, 45)

    def test_sathapana_khr(self):
        """Test Sathapana KHR message"""
        message = "The amount 8000.00 KHR is paid from VENG TANGHAV, ACLEDA Bank Plc., Bill No.: 52820607604 | KHQR on 2025-10-09 07.58.21 AM with Transaction ID: 099QORT252820557, Hash: 47c04893, Shop-name: Dariya Restaurant"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"SathapanaBank_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 8000.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 9)
        self.assertEqual(trx_time.hour, 7)
        self.assertEqual(trx_time.minute, 58)
        self.assertEqual(trx_time.second, 21)


class TestChipMongBankParser(unittest.TestCase):
    """Tests for chipmongbankpaymentbot parser (parse_chipmong)"""

    def test_chipmong_khr(self):
        """Test Chip Mong KHR message"""
        message = "KHR 6,500 is paid by ABA Bank via KHQR for purchase d0ab71cd. From ANDREW STEPHEN WARNER, at TIN KIMCHHE, date Oct 11, 2025 11:28 AM"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"chipmongbankpaymentbot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 6500)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 11)
        self.assertEqual(trx_time.minute, 28)

    def test_chipmong_usd(self):
        """Test Chip Mong USD message"""
        message = "USD 15.00 is paid by ACLEDA Bank Plc. via KHQR for purchase b89674e9. From CHRON HOKLENG, at Phe Chhunnaroen, date Oct 10, 2025 08:00 PM"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"chipmongbankpaymentbot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 15.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 10)
        self.assertEqual(trx_time.hour, 20)
        self.assertEqual(trx_time.minute, 0)


class TestPRASACBankParser(unittest.TestCase):
    """Tests for prasac_merchant_payment_bot parser (parse_prasac)"""

    def test_prasac_usd(self):
        """Test PRASAC USD message"""
        message = """Received Payment Amount 4.75 USD
- Paid by: RASIN NY / ABA Bank
- Shop ID: 12003630 / Shop Name: Chhuon Sovannchhai
- Counter: Counter 1
- Received by: -
- Transaction Date: 11-Oct-25 09:43.44 AM"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"prasac_merchant_payment_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 4.75)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 9)
        self.assertEqual(trx_time.minute, 43)
        self.assertEqual(trx_time.second, 44)

    def test_prasac_khr(self):
        """Test PRASAC KHR message"""
        message = """Received Payment Amount 48,000 KHR
- Paid by: HOUT DO / ABA Bank
- Shop ID: 12003630 / Shop Name: Chhuon Sovannchhai
- Counter: Counter 1
- Received by: -
- Transaction Date: 11-Oct-25 10:12.41 AM"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"prasac_merchant_payment_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 48000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 12)
        self.assertEqual(trx_time.second, 41)


class TestAMKBankParser(unittest.TestCase):
    """Tests for AMKPlc_bot parser (parse_amk)"""

    def test_amk_khr(self):
        """Test AMK KHR message"""
        message = """**AMK PAY**
**KHR 10,000** is paid from **THAK, CHHORN** to **RANN, DANIEL** on **15-09-2025 04:17 PM** with Transaction ID: **17579278527470001**"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"AMKPlc_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 10000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 9)
        self.assertEqual(trx_time.day, 15)
        self.assertEqual(trx_time.hour, 16)
        self.assertEqual(trx_time.minute, 17)


class TestPrinceBankParser(unittest.TestCase):
    """Tests for prince_pay_bot parser (parse_prince)"""

    def test_prince_usd(self):
        """Test Prince Bank USD message"""
        message = """Dear valued customer, you have received a payment:
Amount: **USD 50.00**
Datetime: 2025/09/26, 10:07 pm
Reference No: 794715018
Merchant name: SOU CHENDA
Received from: **Sou Chenda**
Sender's bank: **ACLEDA Bank Plc.**
Hash: ab32be50"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"prince_pay_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 50.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 9)
        self.assertEqual(trx_time.day, 26)
        self.assertEqual(trx_time.hour, 22)
        self.assertEqual(trx_time.minute, 7)

    def test_prince_khr(self):
        """Test Prince Bank KHR message"""
        message = """Dear valued customer, you have received a payment:
Amount: **KHR 1,129,000**
Datetime: 2025/10/10, 10:36 pm
Reference No: 820162501
Merchant name: SOU CHENDA
Received from: **Sok Samaun**
Sender's bank: **ACLEDA Bank Plc.**
Hash: c9b37f6d"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"prince_pay_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 1129000)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 10)
        self.assertEqual(trx_time.hour, 22)
        self.assertEqual(trx_time.minute, 36)


class TestS7POSParser(unittest.TestCase):
    """Tests for s7pos_bot parser (parse_s7pos)"""

    def test_s7pos_khmer_format(self):
        """Test S7POS Khmer format message"""
        message = """**ការ​ក​ម្ម​ង់​ថ្មី INV/127948**
Seng Panhasak
069631070
វិមានឯករាជ្យ
ថ្ងៃ: 2025-10-11 10:58:00
ការកម្មង់
ក្តិបកាបូប Longcharm  X1  5 $
មួកចាក់ 5$  X1  5 $
សរុប: 10.00 $
បញ្ចុះតំលៃ: 0.00 $
សរុបចុងក្រោយ: 10.00 $
អ្នកលក់: smlshopcashier"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"s7pos_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.00)
        self.assertIsNotNone(trx_time)
        self.assertEqual(trx_time.year, 2025)
        self.assertEqual(trx_time.month, 10)
        self.assertEqual(trx_time.day, 11)
        self.assertEqual(trx_time.hour, 10)
        self.assertEqual(trx_time.minute, 58)
        self.assertEqual(trx_time.second, 0)


class TestS7DaysParser(unittest.TestCase):
    """Tests for S7days777 parser (parse_s7days)"""

    def test_s7days_summary(self):
        """Test S7days summary message with multiple USD values"""
        message = """10.10.2025
•Shift:C

-Time:11.00-pm -7:00am
-Total available room= 51
-Room Sold = 27
-Booking = 0
-Total Remain room = 22
-Selected Premium Double = 0
-Deluxe Double = 10
-Premium Double = 3
-Deluxe Twin = 2
-Premium Twin = 7
-Room blocks = (311&214)
-Short Time = 0
-Cash = 0$
-Other Income = 0$
-Cash outlay = 0$
-Total Room Revenues =20$
-OTA =  (alipay) = 0$
-Agoda = 0$
-Ctrip: = 0$
-Bank Card = 20$
-expenses = 0$

•Shift D

-Cash: = 74.6$
-Cash Outlay: 0$
-Total Room Revenue = 74.6$
-Expenses = 0
-Expedia = 0
-Bank Card = 0$
-Alipay = 0$
-Pipay = 0$
-Ctrip: = 0$
-Agoda: = 0$
-Name    : Soeun Theara & Theng ra yuth"""
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"S7days777")
        self.assertEqual(currency, '$')
        # Sum of all USD values: 0+0+0+20+0+0+0+20+0 + 74.6+0+74.6+0+0+0+0+0+0+0 = 189.2
        self.assertAlmostEqual(amount, 189.2, places=2)


class TestPaymentBKParser(unittest.TestCase):
    """Tests for payment_bk_bot parser (parse_payment_bk)"""

    def test_payment_bk_fallback(self):
        """Test payment_bk_bot uses fallback (no sample available)"""
        # No sample message available, test that it falls back to universal parser
        message = "10.00 USD payment received"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"payment_bk_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.00)


class TestUnknownBotFallback(unittest.TestCase):
    """Tests for unknown bot fallback to universal parser"""

    def test_unknown_bot_universal_parser(self):
        """Test unknown bot uses universal parser"""
        message = "$50.25 Transaction completed"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"unknown_bot_123")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 50.25)

    def test_unknown_bot_khmer_pattern(self):
        """Test unknown bot with Khmer pattern"""
        message = "ចំនួន 11,500 រៀល បានទទួល"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message,"unknown_bot_xyz")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 11500)


class TestPaidByFieldExtraction(unittest.TestCase):
    """Tests for paid_by field extraction from messages"""

    def test_aba_english_paid_by_extraction(self):
        """Test ABA English message extracts paid_by field"""
        message = "$28.00 paid by HORN SAMIV (*708) on Nov 09, 03:02 AM via ABA PAY at LIM LONG VOASOR by C.VA. Trx. ID: 176263217516039, APV: 663775."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 28.00)
        self.assertEqual(paid_by, '708')
        self.assertIsNotNone(trx_time)

    def test_aba_khmer_paid_by_extraction(self):
        """Test ABA Khmer message extracts paid_by field"""
        message = "$17.50 ត្រូវបានបង់ដោយ TRY SOPHEA (*332) នៅថ្ងៃទី 9 ខែវិច្ឆិកា ឆ្នាំ 2025 ម៉ោង 02:55 តាម ABA PAY នៅ SAN SREYMOM។ លេខប្រតិបត្តិការ: 176263171918462។ APV: 241904។"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 17.50)
        self.assertEqual(paid_by, '332')

    def test_paid_by_with_different_account_numbers(self):
        """Test paid_by extraction with various account numbers"""
        test_cases = [
            ("$10.00 paid by USER A (*123) on Oct 11", "123"),
            ("$20.00 paid by USER B (*456) via ABA PAY", "456"),
            ("$30.00 ត្រូវបានបង់ដោយ USER C (*789) នៅថ្ងៃទី 9", "789"),
            ("៛50,000 paid by USER D (*001) on Nov 09", "001"),
            ("$100.00 paid by USER E (*999) via ABA", "999"),
        ]

        for message, expected_paid_by in test_cases:
            with self.subTest(message=message):
                currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "PayWayByABA_bot")
                self.assertEqual(paid_by, expected_paid_by)

    def test_paid_by_not_found(self):
        """Test paid_by is None when account number pattern is not found"""
        message = "Received 10.50 USD from John Doe, 11-Oct-2025 10:12AM."
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "ACLEDABankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.50)
        self.assertIsNone(paid_by)

    def test_paid_by_universal_parser(self):
        """Test paid_by extraction works with universal parser"""
        message = "$25.00 paid by TEST USER (*555) transaction completed"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "unknown_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 25.00)
        self.assertEqual(paid_by, '555')

    def test_paid_by_multiple_patterns_in_message(self):
        """Test paid_by extraction when multiple (*XXX) patterns exist"""
        # Should extract the first occurrence
        message = "$15.00 paid by USER (*123) to MERCHANT (*456) on Nov 09"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(paid_by, '123')

    def test_paid_by_edge_cases(self):
        """Test paid_by extraction with edge cases"""
        # Test with leading zeros
        message1 = "$10.00 paid by USER (*001) on Nov 09"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message1, "PayWayByABA_bot")
        self.assertEqual(paid_by, '001')

        # Test with all same digits
        message2 = "៛20,000 paid by USER (*777) via ABA"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message2, "PayWayByABA_bot")
        self.assertEqual(paid_by, '777')

        # Test with sequential digits
        message3 = "$30.00 paid by USER (*012) on Oct 11"
        currency, amount, trx_time, paid_by, _ = extract_amount_currency_and_time(message3, "PayWayByABA_bot")
        self.assertEqual(paid_by, '012')


class TestPaidByNameExtraction(unittest.TestCase):
    """Tests for paid_by_name field extraction with Khmer and English support"""

    def test_english_name_english_message(self):
        """Test English name extraction from English message"""
        message = "៛14,000 paid by CHOR SEIHA (*655) on Oct 11, 10:21 AM via ABA PAY at KEAM LILAY."
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 14000)
        self.assertEqual(paid_by, '655')
        self.assertEqual(paid_by_name, 'CHOR SEIHA')

    def test_khmer_name_english_message(self):
        """Test Khmer name extraction from English message with 'paid by'"""
        message = "៛14,000 paid by ពៅ សុនី (*670) on Nov 21, 11:20 PM via ABA KHQR (ACLEDA Bank Plc.) at HEN NEANG. Trx. ID: 176374200094510, APV: 903085."
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 14000)
        self.assertEqual(paid_by, '670')
        self.assertEqual(paid_by_name, 'ពៅ សុនី')

    def test_english_name_khmer_message(self):
        """Test English name extraction from Khmer message with 'ត្រូវបានបង់ដោយ'"""
        message = "$17.50 ត្រូវបានបង់ដោយ KHAN SAMBO (*435) នៅថ្ងៃទី 21 ខែវិច្ឆិកា ឆ្នាំ 2025 ម៉ោង 22:58 តាម ABA PAY នៅ SAN SREYMOM។ លេខប្រតិបត្តិការ: 176374069457467។ APV: 700323។"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 17.50)
        self.assertEqual(paid_by, '435')
        self.assertEqual(paid_by_name, 'KHAN SAMBO')

    def test_khmer_name_khmer_message(self):
        """Test Khmer name extraction from Khmer message"""
        message = "៛10,400 ត្រូវបានបង់ដោយ ចាន់ ធីតា (*111) នៅថ្ងៃទី 11 ខែតុលា ឆ្នាំ 2025 ម៉ោង 10:15 តាម ABA PAY នៅ STORE។"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 10400)
        self.assertEqual(paid_by, '111')
        self.assertEqual(paid_by_name, 'ចាន់ ធីតា')

    def test_name_with_aba_bank_suffix(self):
        """Test name extraction with ABA Bank suffix"""
        message = "105.00 USD is paid by SOYANUK SAMOEURN, ABA Bank *3961 on 31-October-2025"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "ccu_bank_bot")
        self.assertEqual(paid_by_name, 'SOYANUK SAMOEURN')

    def test_name_with_parentheses_bank(self):
        """Test name extraction with bank in parentheses"""
        message = "4,000 KHR was credited by CHANRAINGSEY NORATH (ABA Bank) via KHQR to Mixue"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PLBITBot")
        self.assertEqual(paid_by_name, 'CHANRAINGSEY NORATH')

    def test_mixed_english_khmer_name(self):
        """Test extraction of name with mixed English and Khmer characters"""
        message = "$10.00 paid by JOHN ចាន់ (*123) on Nov 21 via ABA PAY"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PayWayByABA_bot")
        self.assertEqual(paid_by, '123')
        self.assertEqual(paid_by_name, 'JOHN ចាន់')

    def test_name_with_multiple_spaces(self):
        """Test name extraction with multiple spaces (should be collapsed)"""
        message = "4,000 KHR was credited by CHANRAINGSEY NORATH                                (ABA Bank) via KHQR"
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "PLBITBot")
        # Multiple spaces should be collapsed to single space
        self.assertEqual(paid_by_name, 'CHANRAINGSEY NORATH')

    def test_name_not_found(self):
        """Test paid_by_name is None when name pattern is not found"""
        message = "Received 10.50 USD from account 123, 11-Oct-2025 10:12AM."
        currency, amount, trx_time, paid_by, paid_by_name = extract_amount_currency_and_time(message, "ACLEDABankBot")
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.50)
        self.assertIsNone(paid_by_name)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
