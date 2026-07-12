-- Migration 003: Fix placeholders $1/$2 in service_fee_templates descriptions
-- Date: 2026-05-25 (updated 2026-07-12: added Pass 2 for bare $1/$2)
-- Author: Tech Lead (RAO-P3-014)
-- Description: Replace placeholders $1/$2 with actual values from amount_from/amount_to
--   Pass 1: Replace "$1 zł" / "$2 zł" (with suffix) → raw amount + " zł"
--   Pass 2: Replace bare "$1" / "$2" (without suffix) → formatted amount + " zł"
--           (e.g. "$1" → "150,00 zł" for diesel preset)

-- Backup before migration
CREATE TABLE IF NOT EXISTS service_fee_templates_backup_20260525 AS SELECT * FROM service_fee_templates;

-- Pass 1: Replace "$1 zł" / "$2 zł" (with suffix)
UPDATE service_fee_templates 
SET description = REPLACE(
    REPLACE(
        description,
        '$1 zł',
        CONCAT(IFNULL(amount_from, ''), ' zł')
    ),
    '$2 zł',
    CONCAT(IFNULL(amount_to, ''), ' zł')
)
WHERE description LIKE '%$1%' OR description LIKE '%$2%';

-- Pass 2: Replace bare "$1" / "$2" (without suffix) → formatted PL amount + " zł"
-- FORMAT(x, 2) gives "150.00" → swap decimal separator → "150,00" → add space for thousands
UPDATE service_fee_templates 
SET description = REPLACE(
    REPLACE(
        description,
        '$1',
        CONCAT(REPLACE(REPLACE(FORMAT(IFNULL(amount_from, 0), 2), ',', ' '), '.', ','), ' zł')
    ),
    '$2',
    CONCAT(REPLACE(REPLACE(FORMAT(IFNULL(amount_to, 0), 2), ',', ' '), '.', ','), ' zł')
)
WHERE description LIKE '%$1%' OR description LIKE '%$2%';

-- Same for contract_service_fees (existing contracts)
UPDATE contract_service_fees 
SET description = REPLACE(
    REPLACE(
        description,
        '$1 zł',
        CONCAT(IFNULL(amount_from, ''), ' zł')
    ),
    '$2 zł',
    CONCAT(IFNULL(amount_to, ''), ' zł')
)
WHERE description LIKE '%$1%' OR description LIKE '%$2%';

UPDATE contract_service_fees 
SET description = REPLACE(
    REPLACE(
        description,
        '$1',
        CONCAT(REPLACE(REPLACE(FORMAT(IFNULL(amount_from, 0), 2), ',', ' '), '.', ','), ' zł')
    ),
    '$2',
    CONCAT(REPLACE(REPLACE(FORMAT(IFNULL(amount_to, 0), 2), ',', ' '), '.', ','), ' zł')
)
WHERE description LIKE '%$1%' OR description LIKE '%$2%';

-- Verify migration
SELECT 
    id, 
    name, 
    description, 
    amount_from, 
    amount_to,
    CASE 
        WHEN description LIKE '%$1%' OR description LIKE '%$2%' THEN 'STILL_HAS_PLACEHOLDERS'
        ELSE 'OK'
    END as status
FROM service_fee_templates
ORDER BY id;

-- Expected result: all rows should have status = 'OK'
