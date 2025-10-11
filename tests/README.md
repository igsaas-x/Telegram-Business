# Test Suite

This directory contains all unit tests for the Telegram Message Listener application.

## Test Files

- **test_message_parser.py** - Tests for the current message parser implementation
- **test_bot_parsers.py** - Tests for the optimized bot-specific parsers (15 bots)

## Running Tests

### Run all tests
```bash
python -m pytest tests/
```

### Run with verbose output
```bash
python -m pytest tests/ -v
```

### Run a specific test file
```bash
python -m pytest tests/test_bot_parsers.py
```

### Run a specific test class
```bash
python -m pytest tests/test_bot_parsers.py::TestACLEDABankParser
```

### Run a specific test method
```bash
python -m pytest tests/test_bot_parsers.py::TestACLEDABankParser::test_acleda_english_usd
```

### Using unittest (alternative)
```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py" -v

# Run a specific test file
python -m unittest tests.test_bot_parsers

# Run a specific test class
python -m unittest tests.test_bot_parsers.TestACLEDABankParser

# Run directly
cd tests
python test_bot_parsers.py
```

## Test Coverage

### Bot-Specific Parser Tests (test_bot_parsers.py)

Tests for all 15 supported bots with real message samples:

1. **ACLEDA Bank** (4 tests) - English + Khmer, USD + KHR
2. **ABA Bank** (4 tests) - English + Khmer, USD + KHR
3. **PLB Bank** (2 tests) - USD + KHR
4. **Canadia Bank** (1 test) - USD only
5. **HLB Bank** (2 tests) - USD + KHR
6. **Vattanac Bank** (2 tests) - USD + KHR
7. **CP Bank** (4 tests) - USD + KHR, multiple formats
8. **Sathapana Bank** (2 tests) - USD + KHR
9. **Chip Mong Bank** (2 tests) - USD + KHR
10. **PRASAC Bank** (2 tests) - USD + KHR
11. **AMK Bank** (1 test) - KHR only
12. **Prince Bank** (2 tests) - USD + KHR
13. **S7POS** (1 test) - Khmer format
14. **S7Days** (1 test) - Summary format
15. **Payment BK** (1 test) - Fallback

**Total: 31 test cases**

### Expected Test Results

All tests should pass with the optimized parser implementation. Each test:
- Uses real message samples from production
- Validates currency symbol extraction
- Validates amount parsing (with comma removal)
- Tests both English and Khmer variants where applicable

## CI/CD Integration

Tests are automatically run on every push and pull request via GitHub Actions.

See `.github/workflows/test.yml` for configuration.
