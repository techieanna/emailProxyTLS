/*******************************************************************************
 * Database Setup Scripts for COMPRATE Validation
 *
 * This file contains DDL and sample data for the configuration tables
 * required by the JOB COMPRATE validation PeopleCode
 *
 * IMPORTANT: Adjust table and field names to match your PeopleSoft naming
 *            conventions and requirements
 ******************************************************************************/

-- =============================================================================
-- 1. SALARY BAND CONFIGURATION TABLE
-- =============================================================================
-- This table stores the maximum (and optionally minimum) salary for each
-- labour agreement. The validation PeopleCode queries this table to determine
-- if a compensation rate change exceeds the allowed maximum.

CREATE TABLE PS_SAL_BAND_CONFIG (
    -- Key Fields
    LABOUR_AGREEMENT    VARCHAR2(10)    NOT NULL,   -- Labour agreement code
    EFFDT               DATE            NOT NULL,   -- Effective date for history tracking

    -- Salary Range Fields
    MAX_SALARY          NUMBER(18,2)    NOT NULL,   -- Maximum salary for this band
    MIN_SALARY          NUMBER(18,2),               -- Optional: Minimum salary

    -- Additional Context Fields (optional)
    CURRENCY_CD         VARCHAR2(3),                -- Currency code (USD, EUR, etc.)
    COUNTRY             VARCHAR2(3),                -- Country code
    DESCR               VARCHAR2(30),               -- Description
    DESCRSHORT          VARCHAR2(10),               -- Short description

    -- Audit Fields (optional)
    LASTUPDDTTM         TIMESTAMP,                  -- Last update timestamp
    LASTUPDOPRID        VARCHAR2(30),               -- Last update operator ID

    -- Primary Key
    CONSTRAINT PS_SAL_BAND_CONFIG_PK PRIMARY KEY (LABOUR_AGREEMENT, EFFDT)
);

-- Index for efficient effective-dated queries
CREATE INDEX PS_SAL_BAND_CONFIG_I1 ON PS_SAL_BAND_CONFIG (LABOUR_AGREEMENT, EFFDT DESC);

-- Comments for documentation
COMMENT ON TABLE PS_SAL_BAND_CONFIG IS 'Salary band configuration for labour agreement validation';
COMMENT ON COLUMN PS_SAL_BAND_CONFIG.LABOUR_AGREEMENT IS 'Labour agreement code from JOB record';
COMMENT ON COLUMN PS_SAL_BAND_CONFIG.MAX_SALARY IS 'Maximum allowed salary for this labour agreement';
COMMENT ON COLUMN PS_SAL_BAND_CONFIG.EFFDT IS 'Effective date for historical tracking';


-- =============================================================================
-- 2. SAMPLE DATA FOR SALARY BAND CONFIG
-- =============================================================================
-- Insert sample configuration data (adjust to your requirements)

INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR)
VALUES ('UNION_A', DATE '2024-01-01', 150000.00, 50000.00, 'USD', 'Union A Salary Band');

INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR)
VALUES ('UNION_B', DATE '2024-01-01', 120000.00, 40000.00, 'USD', 'Union B Salary Band');

INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR)
VALUES ('UNION_C', DATE '2024-01-01', 100000.00, 35000.00, 'USD', 'Union C Salary Band');

INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR)
VALUES ('MGMT', DATE '2024-01-01', 250000.00, 80000.00, 'USD', 'Management Salary Band');

INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR)
VALUES ('EXEC', DATE '2024-01-01', 500000.00, 150000.00, 'USD', 'Executive Salary Band');

COMMIT;


-- =============================================================================
-- 3. JPM_JP_ITEMS TABLE (Audit/Lock Table)
-- =============================================================================
-- This table stores records when a compensation rate exceeds the maximum
-- allowed salary. Each record represents a validation failure that needs
-- review or approval.

CREATE TABLE PS_JPM_JP_ITEMS (
    -- Key Fields
    EMPLID              VARCHAR2(11)    NOT NULL,   -- Employee ID
    EMPL_RCD            NUMBER(3)       NOT NULL,   -- Employee record number
    ITEM_TYPE           VARCHAR2(15)    NOT NULL,   -- Item type (e.g., 'SRK_OVT_LOCK')
    ITEM_NBR            NUMBER(10)      NOT NULL,   -- Sequence number for this item

    -- Validation Context Fields
    COMPRATE            NUMBER(18,2),               -- The compensation rate that exceeded limit
    MAX_SALARY          NUMBER(18,2),               -- The maximum salary that was exceeded
    LABOUR_AGREEMENT    VARCHAR2(10),               -- Labour agreement used for validation

    -- Additional Context (optional)
    JOBCODE             VARCHAR2(13),               -- Job code at time of violation
    POSITION_NBR        VARCHAR2(10),               -- Position number
    DEPTID              VARCHAR2(10),               -- Department ID
    BUSINESS_UNIT       VARCHAR2(5),                -- Business unit

    -- Status and Workflow Fields
    STATUS              VARCHAR2(1),                -- Status: N=New, A=Approved, R=Rejected, C=Cancelled
    CREATE_DTTM         TIMESTAMP,                  -- When record was created
    OPRID               VARCHAR2(30),               -- Operator who triggered the validation

    -- Review/Approval Fields
    REVIEWER_ID         VARCHAR2(11),               -- ID of reviewer/approver
    REVIEW_DTTM         TIMESTAMP,                  -- When reviewed/approved
    REVIEW_COMMENTS     VARCHAR2(254),              -- Reviewer comments

    -- Audit Fields
    LASTUPDDTTM         TIMESTAMP,                  -- Last update timestamp
    LASTUPDOPRID        VARCHAR2(30),               -- Last update operator

    -- Primary Key
    CONSTRAINT PS_JPM_JP_ITEMS_PK PRIMARY KEY (EMPLID, EMPL_RCD, ITEM_TYPE, ITEM_NBR)
);

-- Indexes for common queries
CREATE INDEX PS_JPM_JP_ITEMS_I1 ON PS_JPM_JP_ITEMS (ITEM_TYPE, STATUS, CREATE_DTTM DESC);
CREATE INDEX PS_JPM_JP_ITEMS_I2 ON PS_JPM_JP_ITEMS (CREATE_DTTM DESC);
CREATE INDEX PS_JPM_JP_ITEMS_I3 ON PS_JPM_JP_ITEMS (REVIEWER_ID, STATUS);
CREATE INDEX PS_JPM_JP_ITEMS_I4 ON PS_JPM_JP_ITEMS (LABOUR_AGREEMENT, STATUS);

-- Comments for documentation
COMMENT ON TABLE PS_JPM_JP_ITEMS IS 'Audit/lock records for salary validation violations';
COMMENT ON COLUMN PS_JPM_JP_ITEMS.ITEM_TYPE IS 'Type of item - SRK_OVT_LOCK for salary over-limit';
COMMENT ON COLUMN PS_JPM_JP_ITEMS.STATUS IS 'N=New, A=Approved, R=Rejected, C=Cancelled';
COMMENT ON COLUMN PS_JPM_JP_ITEMS.COMPRATE IS 'Compensation rate that triggered the violation';


-- =============================================================================
-- 4. SEQUENCE FOR ITEM_NBR (Optional)
-- =============================================================================
-- If you want to use a sequence instead of MAX(ITEM_NBR)+1 approach

CREATE SEQUENCE PS_JPM_ITEM_SEQ
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- Grant usage if needed
-- GRANT SELECT ON PS_JPM_ITEM_SEQ TO PEOPLESOFT_APP_USER;


-- =============================================================================
-- 5. USEFUL QUERIES FOR MONITORING AND MAINTENANCE
-- =============================================================================

-- Query 1: View all pending violations (need review)
-- Use this to see all compensation changes that exceeded the limit and are
-- awaiting review/approval
/*
SELECT
    j.EMPLID,
    j.NAME,
    j.EMPL_RCD,
    j.LABOUR_AGREEMENT,
    j.COMPRATE,
    j.MAX_SALARY,
    j.COMPRATE - j.MAX_SALARY AS OVER_LIMIT_AMOUNT,
    j.CREATE_DTTM,
    j.ITEM_NBR
FROM PS_JPM_JP_ITEMS j
WHERE j.ITEM_TYPE = 'SRK_OVT_LOCK'
  AND j.STATUS = 'N'  -- New/Pending
ORDER BY j.CREATE_DTTM DESC;
*/

-- Query 2: Count violations by labour agreement
-- Use this to identify which labour agreements have the most violations
/*
SELECT
    LABOUR_AGREEMENT,
    COUNT(*) AS VIOLATION_COUNT,
    AVG(COMPRATE - MAX_SALARY) AS AVG_EXCESS,
    MAX(COMPRATE - MAX_SALARY) AS MAX_EXCESS
FROM PS_JPM_JP_ITEMS
WHERE ITEM_TYPE = 'SRK_OVT_LOCK'
  AND STATUS = 'N'
GROUP BY LABOUR_AGREEMENT
ORDER BY VIOLATION_COUNT DESC;
*/

-- Query 3: Violations requiring urgent review (>30 days old)
-- Use this to find violations that have been pending too long
/*
SELECT
    j.EMPLID,
    j.EMPL_RCD,
    j.LABOUR_AGREEMENT,
    j.COMPRATE,
    j.MAX_SALARY,
    j.CREATE_DTTM,
    TRUNC(SYSDATE - j.CREATE_DTTM) AS DAYS_PENDING
FROM PS_JPM_JP_ITEMS j
WHERE j.ITEM_TYPE = 'SRK_OVT_LOCK'
  AND j.STATUS = 'N'
  AND j.CREATE_DTTM < SYSDATE - 30
ORDER BY j.CREATE_DTTM ASC;
*/

-- Query 4: Approved exceptions (for reporting)
-- Use this to see which violations were approved and by whom
/*
SELECT
    j.EMPLID,
    j.LABOUR_AGREEMENT,
    j.COMPRATE,
    j.MAX_SALARY,
    j.COMPRATE - j.MAX_SALARY AS APPROVED_EXCESS,
    j.REVIEWER_ID,
    j.REVIEW_DTTM,
    j.REVIEW_COMMENTS
FROM PS_JPM_JP_ITEMS j
WHERE j.ITEM_TYPE = 'SRK_OVT_LOCK'
  AND j.STATUS = 'A'  -- Approved
ORDER BY j.REVIEW_DTTM DESC;
*/

-- Query 5: Update salary band maximum (effective-dated)
-- Use this to create a new effective-dated row when salary bands change
/*
INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, DESCR, LASTUPDDTTM, LASTUPDOPRID)
SELECT
    LABOUR_AGREEMENT,
    DATE '2025-01-01' AS EFFDT,  -- New effective date
    MAX_SALARY * 1.05 AS MAX_SALARY,  -- 5% increase
    MIN_SALARY * 1.05 AS MIN_SALARY,  -- 5% increase
    CURRENCY_CD,
    DESCR,
    SYSTIMESTAMP AS LASTUPDDTTM,
    'ADMIN' AS LASTUPDOPRID
FROM PS_SAL_BAND_CONFIG
WHERE EFFDT = (SELECT MAX(EFFDT) FROM PS_SAL_BAND_CONFIG WHERE LABOUR_AGREEMENT = PS_SAL_BAND_CONFIG.LABOUR_AGREEMENT);

COMMIT;
*/


-- =============================================================================
-- 6. CLEANUP SCRIPTS (Use with caution!)
-- =============================================================================

-- Delete all test data from JPM_JP_ITEMS
-- CAUTION: Only use in development/testing environments!
/*
DELETE FROM PS_JPM_JP_ITEMS WHERE ITEM_TYPE = 'SRK_OVT_LOCK';
COMMIT;
*/

-- Reset sequence (if using sequence for ITEM_NBR)
/*
DROP SEQUENCE PS_JPM_ITEM_SEQ;
CREATE SEQUENCE PS_JPM_ITEM_SEQ START WITH 1 INCREMENT BY 1;
*/


-- =============================================================================
-- 7. GRANT PERMISSIONS (Adjust based on your security model)
-- =============================================================================

-- Grant permissions to PeopleSoft application user
-- Replace 'PS_USER' with your actual PeopleSoft application user
/*
GRANT SELECT, INSERT, UPDATE ON PS_SAL_BAND_CONFIG TO PS_USER;
GRANT SELECT, INSERT, UPDATE ON PS_JPM_JP_ITEMS TO PS_USER;
GRANT SELECT ON PS_JPM_ITEM_SEQ TO PS_USER;
*/


-- =============================================================================
-- 8. VALIDATION QUERIES (Run these to verify setup)
-- =============================================================================

-- Verify salary band config data exists
SELECT COUNT(*) AS CONFIG_COUNT FROM PS_SAL_BAND_CONFIG;

-- Verify JPM_JP_ITEMS table is empty (before go-live)
SELECT COUNT(*) AS ITEMS_COUNT FROM PS_JPM_JP_ITEMS;

-- Test query for effective-dated config (should return correct row)
SELECT LABOUR_AGREEMENT, MAX_SALARY, EFFDT
FROM PS_SAL_BAND_CONFIG
WHERE LABOUR_AGREEMENT = 'UNION_A'
  AND EFFDT = (SELECT MAX(EFFDT)
               FROM PS_SAL_BAND_CONFIG
               WHERE LABOUR_AGREEMENT = 'UNION_A'
               AND EFFDT <= SYSDATE);


/*******************************************************************************
 * NOTES:
 *
 * 1. Table Names: Add 'PS_' prefix if following PeopleSoft naming convention
 * 2. Effective Dating: Consider whether PS_SAL_BAND_CONFIG needs effective dating
 * 3. Currency: Add currency handling if you have multi-currency requirements
 * 4. Security: Ensure proper grants and row-level security if needed
 * 5. Indexes: Monitor query performance and add indexes as needed
 * 6. Partitioning: Consider partitioning PS_JPM_JP_ITEMS if high volume
 * 7. Archival: Plan for archiving old/completed records from PS_JPM_JP_ITEMS
 *
 ******************************************************************************/
