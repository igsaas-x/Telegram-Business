-- ========================================
-- Parse ABA Sender Names from Existing Messages
-- ========================================
-- This script extracts sender names from ABA bank messages
-- and updates the paid_by_name column in income_balance table
--
-- Target: Last 3 days of messages for chat_id = -1002875564121
--
-- Usage:
--   mysql -u your_user -p your_database < parse_aba_sender_names.sql
-- ========================================

-- Set variables
SET @chat_id = -1002875564121;
SET @days_back = 3;

-- Preview what will be updated (uncomment to check before running)
-- SELECT
--     id,
--     message_id,
--     income_date,
--     paid_by,
--     paid_by_name AS current_paid_by_name,
--     -- Extract name using REGEXP_SUBSTR (MySQL 8.0+)
--     CASE
--         -- English "paid by NAME (*XXX)"
--         WHEN message REGEXP 'paid by [A-Z][A-Z0-9 \u1780-\u17FF]+\\(\\*[0-9]{3}\\)' THEN
--             TRIM(REGEXP_SUBSTR(message, 'paid by ([A-Z][A-Z0-9 \u1780-\u17FF]+)\\s*\\(\\*[0-9]{3}\\)', 1, 1, '', 1))
--         -- Khmer "ត្រូវបានបង់ដោយ NAME (*XXX)"
--         WHEN message REGEXP 'ត្រូវបានបង់ដោយ [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+\\(\\*[0-9]{3}\\)' THEN
--             TRIM(REGEXP_SUBSTR(message, 'ត្រូវបានបង់ដោយ ([A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+)\\s*\\(\\*[0-9]{3}\\)', 1, 1, '', 1))
--         -- English "paid by NAME, ABA Bank"
--         WHEN message REGEXP 'paid by [A-Z][A-Z ]+, ABA Bank' THEN
--             TRIM(REGEXP_SUBSTR(message, 'paid by ([A-Z][A-Z ]+), ABA Bank', 1, 1, '', 1))
--         -- English "paid by NAME (ABA Bank)"
--         WHEN message REGEXP 'paid by [A-Z][A-Z ]+ \\(ABA Bank\\)' THEN
--             TRIM(REGEXP_SUBSTR(message, 'paid by ([A-Z][A-Z ]+) \\(ABA Bank\\)', 1, 1, '', 1))
--         -- English "credited by NAME (ABA Bank)"
--         WHEN message REGEXP 'credited by [A-Z][A-Z ]+\\s+\\(ABA Bank\\)' THEN
--             TRIM(REGEXP_SUBSTR(message, 'credited by ([A-Z][A-Z ]+)\\s+\\(ABA Bank\\)', 1, 1, '', 1))
--         ELSE NULL
--     END AS extracted_name,
--     LEFT(message, 100) AS message_preview
-- FROM income_balance
-- WHERE chat_id = @chat_id
--     AND income_date >= DATE_SUB(NOW(), INTERVAL @days_back DAY)
--     AND (message LIKE '%paid by%' OR message LIKE '%ត្រូវបានបង់ដោយ%' OR message LIKE '%credited by%')
--     AND paid_by IS NOT NULL
-- ORDER BY income_date DESC;

-- ========================================
-- UPDATE Statement
-- ========================================
-- This updates the paid_by_name column with extracted sender names

UPDATE income_balance
SET paid_by_name = CASE
    -- Pattern 1: English "paid by NAME (*XXX)" - with Khmer support
    WHEN message REGEXP 'paid by [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+\\(\\*[0-9]{3}\\)' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'paid by [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+\\s*\\(\\*[0-9]{3}\\)'),
            'paid by ([A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+)\\s*\\(\\*[0-9]{3}\\)',
            '\\1'
        ))

    -- Pattern 2: Khmer "ត្រូវបានបង់ដោយ NAME (*XXX)"
    WHEN message REGEXP 'ត្រូវបានបង់ដោយ [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+\\(\\*[0-9]{3}\\)' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'ត្រូវបានបង់ដោយ [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+\\s*\\(\\*[0-9]{3}\\)'),
            'ត្រូវបានបង់ដោយ ([A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+)\\s*\\(\\*[0-9]{3}\\)',
            '\\1'
        ))

    -- Pattern 3: English "paid by NAME, ABA Bank"
    WHEN message REGEXP 'paid by [A-Z][A-Z ]+, ABA Bank' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'paid by [A-Z][A-Z ]+, ABA Bank'),
            'paid by ([A-Z][A-Z ]+), ABA Bank',
            '\\1'
        ))

    -- Pattern 4: English "paid by NAME (ABA Bank)"
    WHEN message REGEXP 'paid by [A-Z][A-Z ]+ \\(ABA Bank\\)' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'paid by [A-Z][A-Z ]+ \\(ABA Bank\\)'),
            'paid by ([A-Z][A-Z ]+) \\(ABA Bank\\)',
            '\\1'
        ))

    -- Pattern 5: English "credited by NAME (ABA Bank)"
    WHEN message REGEXP 'credited by [A-Z][A-Z ]+\\s+\\(ABA Bank\\)' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'credited by [A-Z][A-Z ]+\\s+\\(ABA Bank\\)'),
            'credited by ([A-Z][A-Z ]+)\\s+\\(ABA Bank\\)',
            '\\1'
        ))

    -- Pattern 6: Khmer "ត្រូវបានបង់ដោយ NAME នៅ"
    WHEN message REGEXP 'ត្រូវបានបង់ដោយ [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+ នៅ' THEN
        TRIM(REGEXP_REPLACE(
            REGEXP_SUBSTR(message, 'ត្រូវបានបង់ដោយ [A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+ នៅ'),
            'ត្រូវបានបង់ដោយ ([A-Z\u1780-\u17FF][A-Z0-9 \u1780-\u17FF]+) នៅ',
            '\\1'
        ))

    ELSE paid_by_name  -- Keep existing value if no match
END
WHERE chat_id = @chat_id
    AND income_date >= DATE_SUB(NOW(), INTERVAL @days_back DAY)
    AND (message LIKE '%paid by%' OR message LIKE '%ត្រូវបានបង់ដោយ%' OR message LIKE '%credited by%')
    AND paid_by IS NOT NULL;

-- ========================================
-- Show results
-- ========================================
SELECT
    COUNT(*) AS total_updated,
    COUNT(CASE WHEN paid_by_name IS NOT NULL THEN 1 END) AS names_extracted,
    COUNT(CASE WHEN paid_by_name IS NULL THEN 1 END) AS names_not_found
FROM income_balance
WHERE chat_id = @chat_id
    AND income_date >= DATE_SUB(NOW(), INTERVAL @days_back DAY)
    AND paid_by IS NOT NULL;

-- Show sample results
SELECT
    id,
    income_date,
    paid_by,
    paid_by_name,
    LEFT(message, 80) AS message_preview
FROM income_balance
WHERE chat_id = @chat_id
    AND income_date >= DATE_SUB(NOW(), INTERVAL @days_back DAY)
    AND paid_by IS NOT NULL
ORDER BY income_date DESC
LIMIT 20;
