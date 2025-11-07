# JOB Component COMPRATE Validation - Implementation Guide

## Overview
This guide provides detailed instructions for implementing compensation rate validation on the PeopleSoft JOB component.

## Event Selection: SaveEdit (Recommended)

### Why SaveEdit is the Best Choice

**SaveEdit Event** is the optimal choice for this validation because:

1. **Timing in Save Process**
   - Fires **before** database updates are committed
   - Occurs **after** field-level edits but **before** row-level processing
   - Allows you to prevent the save transaction if validation fails

2. **Access to Data**
   - Can access both current and prior values using `PriorValue()`
   - Full access to all component data
   - Can execute SQL queries reliably

3. **User Experience**
   - Validation happens at save time (not too early, not too late)
   - User gets immediate feedback with option to correct
   - Transaction is atomic (either all saves or none saves)

4. **Return Value Control**
   - Return `True` to allow save to proceed
   - Return `False` to abort save and keep user on page
   - Can display error messages to explain why save was blocked

### Event Comparison Matrix

| Event | When It Fires | Can Access PriorValue? | Can Prevent Save? | Best For |
|-------|---------------|------------------------|-------------------|----------|
| **FieldChange** | When field value changes in UI | ❌ No | ❌ No | Real-time UI updates, dependent field calculations |
| **FieldEdit** | On field exit/validation | ⚠️ Limited | ✅ Yes (field level) | Field-level validation, format checks |
| **SaveEdit** | Before save, after field edits | ✅ Yes | ✅ Yes (transaction level) | **Complex validations, cross-field checks** ⭐ |
| **SavePreChg** | After SaveEdit, before DB update | ✅ Yes | ❌ No | Audit logging, auto-population of fields |
| **SavePostChg** | After successful DB update | ❌ No (already saved) | ❌ No | Post-save processing, notifications |

### Recommendation

**Use SaveEdit on the JOB component record** for your implementation because:
- ✅ You need to detect changes (requires `PriorValue()`)
- ✅ You need to validate against database table (config table)
- ✅ You want to prevent save if validation fails
- ✅ You want to insert audit record (JPM_JP_ITEMS) only when validation fails

**Optional: Add SavePreChg** if you want to:
- Log ALL comprate changes (not just violations)
- Ensure JPM_JP_ITEMS record is always created even if other errors occur

## Implementation Steps

### Step 1: Locate the JOB Component in Application Designer

1. Open **PeopleSoft Application Designer**
2. Go to **File > Open > Component**
3. Navigate to the JOB component (typically in HR module)
   - Common paths: `ADMINISTER_WORKFORCE > JOB_DATA` or similar
4. Identify the main record (usually `JOB` or `PS_JOB`)

### Step 2: Add SaveEdit PeopleCode

1. In the component, locate the **Component Record** (usually JOB record)
2. Right-click the record name > **View PeopleCode**
3. Select **SaveEdit** event from dropdown
4. Copy the PeopleCode from `JOB_COMPRATE_VALIDATION.pcode`
5. **Adjust field names** to match your JOB record structure:
   - `COMPRATE` - your compensation rate field name
   - `LABOUR_AGREEMENT` - your labour agreement field (might be `SAL_ADMIN_PLAN`, `UNION_CD`, etc.)
   - `EMPLID`, `EMPL_RCD` - standard fields

### Step 3: Verify Configuration Table

Ensure your salary band configuration table exists and is populated:

```sql
-- Example table structure (adjust to your naming convention)
CREATE TABLE PS_SAL_BAND_CONFIG (
    LABOUR_AGREEMENT VARCHAR2(10) NOT NULL,
    MAX_SALARY       NUMBER(18,2) NOT NULL,
    MIN_SALARY       NUMBER(18,2),
    CURRENCY_CD      VARCHAR2(3),
    EFFDT            DATE,
    PRIMARY KEY (LABOUR_AGREEMENT, EFFDT)
);

-- Sample data
INSERT INTO PS_SAL_BAND_CONFIG VALUES ('UNION_A', 150000.00, 50000.00, 'USD', SYSDATE);
INSERT INTO PS_SAL_BAND_CONFIG VALUES ('UNION_B', 120000.00, 40000.00, 'USD', SYSDATE);
```

**Adjust the SQL query in the PeopleCode** if your table has effective dating:

```javascript
/* Original query */
&sqlConfig = CreateSQL("SELECT MAX_SALARY FROM PS_SAL_BAND_CONFIG WHERE LABOUR_AGREEMENT = :1",
                       &labourAgreement);

/* Effective-dated version */
&sqlConfig = CreateSQL("SELECT MAX_SALARY FROM PS_SAL_BAND_CONFIG
                        WHERE LABOUR_AGREEMENT = :1
                        AND EFFDT = (SELECT MAX(EFFDT) FROM PS_SAL_BAND_CONFIG
                                     WHERE LABOUR_AGREEMENT = :2 AND EFFDT <= :3)",
                       &labourAgreement, &labourAgreement, %Date);
```

### Step 4: Verify/Create JPM_JP_ITEMS Table

Ensure the audit table exists:

```sql
-- Example table structure (adjust to your requirements)
CREATE TABLE PS_JPM_JP_ITEMS (
    EMPLID           VARCHAR2(11) NOT NULL,
    EMPL_RCD         NUMBER(3) NOT NULL,
    ITEM_TYPE        VARCHAR2(15) NOT NULL,
    ITEM_NBR         NUMBER(10) NOT NULL,
    COMPRATE         NUMBER(18,2),
    MAX_SALARY       NUMBER(18,2),
    LABOUR_AGREEMENT VARCHAR2(10),
    CREATE_DTTM      TIMESTAMP,
    STATUS           VARCHAR2(1),
    REVIEWER_ID      VARCHAR2(11),
    REVIEW_DTTM      TIMESTAMP,
    PRIMARY KEY (EMPLID, EMPL_RCD, ITEM_TYPE, ITEM_NBR)
);
```

**Adjust the INSERT statement** in the PeopleCode to match your actual table structure.

### Step 5: Test the Implementation

#### Test Case 1: Valid Change (Below Maximum)
1. Open an employee's JOB data
2. Change COMPRATE to a value **below** the max salary for their labour agreement
3. Save
4. **Expected**: Save succeeds without error
5. **Verify**: No record inserted in JPM_JP_ITEMS

#### Test Case 2: Invalid Change (Exceeds Maximum)
1. Open an employee's JOB data
2. Change COMPRATE to a value **above** the max salary
3. Save
4. **Expected**:
   - Error message displays showing the violation
   - Save is blocked (stays on page)
   - Record IS inserted in JPM_JP_ITEMS with ITEM_TYPE='SRK_OVT_LOCK'
5. **Verify**: Query JPM_JP_ITEMS to confirm record exists

#### Test Case 3: No Change to COMPRATE
1. Open an employee's JOB data
2. Change a different field (e.g., JOBCODE)
3. Save
4. **Expected**: Save succeeds without validation running
5. **Verify**: No record in JPM_JP_ITEMS

#### Test Case 4: Missing Configuration
1. Open an employee with a labour agreement NOT in PS_SAL_BAND_CONFIG
2. Change COMPRATE
3. Save
4. **Expected**: Message about missing configuration
5. **Decide**: Should this allow or block save? Adjust PeopleCode accordingly

### Step 6: Optimization Considerations

#### Performance Optimization
If you have high transaction volume, consider:

```javascript
/* Cache configuration in application session */
Local Rowset &rsConfigCache = GetLevel0()(1).GetRowset(Scroll.SAL_BAND_CONFIG);

/* Or use Derived/Work record to cache during component load */
```

#### Error Handling Enhancement

```javascript
Try
   &sqlInsert.Execute(&emplid, &emplrcd, &itemType, &nextItemNbr,
                      &newComprate, &maxSalary, &labourAgreement);
Catch Exception &ex
   /* Log the error and still prevent save */
   MessageBox(0, "", 0, 0, "Error logging validation failure: " | &ex.ToString());
   /* Still return False to prevent save */
End-Try;
```

#### Multi-Currency Support

```javascript
/* Get currency code from JOB record */
&currencyCd = &rs.GetField(Field.CURRENCY_CD).Value;

/* Query config with currency filter */
&sqlConfig = CreateSQL("SELECT MAX_SALARY FROM PS_SAL_BAND_CONFIG
                        WHERE LABOUR_AGREEMENT = :1 AND CURRENCY_CD = :2",
                       &labourAgreement, &currencyCd);
```

## Alternative Implementations

### Option A: Soft Validation (Warning Only)

If you want to **allow the save but warn the user**:

```javascript
/* In SaveEdit or SavePostChg */
If &newComprate > &maxSalary Then
   /* Insert audit record */
   &sqlInsert.Execute(...);

   /* Display warning but don't prevent save */
   Warning("Compensation Rate exceeds maximum. A review record has been created.");
   /* Do NOT return False - allow save to continue */
End-If;
```

### Option B: Deferred Approval Workflow

If you want to **allow save but trigger approval**:

```javascript
/* Use SavePostChg event */
If &newComprate > &maxSalary Then
   /* Insert JPM_JP_ITEMS record */
   &sqlInsert.Execute(...);

   /* Trigger workflow/approval process */
   /* Example: Call workflow PeopleCode or Integration Broker */
   TriggerApprovalWorkflow(&emplid, &emplrcd, &itemType, &nextItemNbr);
End-If;
```

### Option C: Three-Tier Validation

If you have **multiple severity levels**:

```javascript
/* Check against multiple thresholds */
If &newComprate > &hardMax Then
   /* Hard stop - prevent save */
   MessageBox(...);
   Return False;
Else If &newComprate > &softMax Then
   /* Warning - allow save */
   Warning("Approaching maximum salary for band");
Else
   /* Within range - no action */
End-If;
```

## Maintenance and Monitoring

### Monitoring JPM_JP_ITEMS Records

```sql
-- Query to see all locked/flagged salary changes
SELECT EMPLID, EMPL_RCD, COMPRATE, MAX_SALARY,
       LABOUR_AGREEMENT, CREATE_DTTM, STATUS
FROM PS_JPM_JP_ITEMS
WHERE ITEM_TYPE = 'SRK_OVT_LOCK'
  AND STATUS = 'N'  -- New/Pending
ORDER BY CREATE_DTTM DESC;

-- Count violations by labour agreement
SELECT LABOUR_AGREEMENT, COUNT(*) as VIOLATION_COUNT
FROM PS_JPM_JP_ITEMS
WHERE ITEM_TYPE = 'SRK_OVT_LOCK'
  AND STATUS = 'N'
GROUP BY LABOUR_AGREEMENT;
```

### Updating Salary Band Configuration

```sql
-- Add effective-dated update
INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, MAX_SALARY, MIN_SALARY, CURRENCY_CD, EFFDT)
VALUES ('UNION_A', 160000.00, 55000.00, 'USD', SYSDATE);
```

## Troubleshooting

### Issue: "Labour Agreement not found"
- **Cause**: Field name mismatch or field doesn't exist on JOB record
- **Fix**: Check actual field name in Application Designer
- **Alternative**: May need to join to JOBCODE_TBL or other reference table

### Issue: Insert into JPM_JP_ITEMS fails
- **Cause**: Table doesn't exist or field mismatch
- **Fix**: Verify table structure matches INSERT statement
- **Debug**: Add Try/Catch around INSERT and log error details

### Issue: Validation doesn't fire
- **Cause**: Event not firing or wrong record
- **Fix**: Verify SaveEdit is on Component Record (not component buffer)
- **Debug**: Add MessageBox at start of function to confirm execution

### Issue: PriorValue() returns 0 or null
- **Cause**: Wrong event or field not loaded in buffer
- **Fix**: Ensure field is on component and properly loaded
- **Alternative**: Track old value in RowInit event

## Security Considerations

1. **SQL Injection Prevention**: Already handled by bound parameters (`:1`, `:2`)
2. **Audit Trail**: JPM_JP_ITEMS provides complete audit of violations
3. **Access Control**: Ensure only HR admins can modify PS_SAL_BAND_CONFIG
4. **Data Privacy**: Consider masking salary data in logs/messages

## Summary

**Best Practice Recommendation:**

1. **Event**: SaveEdit on JOB component record
2. **Validation**: Check COMPRATE against PS_SAL_BAND_CONFIG.MAX_SALARY
3. **Action on Violation**:
   - Insert record in JPM_JP_ITEMS with ITEM_TYPE='SRK_OVT_LOCK'
   - Display error message to user
   - Return False to prevent save
4. **Testing**: Comprehensive test cases covering all scenarios
5. **Monitoring**: Regular review of JPM_JP_ITEMS records

This approach ensures data integrity, provides audit trail, and gives users clear feedback while maintaining transaction consistency.
