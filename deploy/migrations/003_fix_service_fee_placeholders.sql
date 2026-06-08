-- Migration 003: Fix placeholders $1/$2 in service_fee_templates descriptions
-- Date: 2026-05-25
-- Author: Tech Lead (RAO-P3-014)
-- Description: Replace placeholders $1/$2 with actual values from amount_from/amount_to

-- Backup before migration
CREATE TABLE IF NOT EXISTS service_fee_templates_backup_20260525 AS SELECT * FROM service_fee_templates;

-- Update descriptions with actual values
-- Pattern: replace $1 with amount_from, $2 with amount_to
-- Format: "X zł" where X is the value formatted as decimal

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
