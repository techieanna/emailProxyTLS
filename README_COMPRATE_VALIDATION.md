# PeopleSoft JOB Component - COMPRATE Validation

## Quick Summary

This solution provides **PeopleCode validation** for the JOB component to detect and control compensation rate changes that exceed configured salary band limits.

### What It Does

1. ✅ Detects when COMPRATE field value changes on JOB component
2. ✅ Validates new salary against maximum from configuration table
3. ✅ Blocks save if salary exceeds limit (configurable behavior)
4. ✅ Creates audit record in JPM_JP_ITEMS table for violations
5. ✅ Provides clear error message to user

### Recommended Event

**SaveEdit** - Best choice for this validation because:
- Fires before database save
- Can access both old and new values
- Can prevent save transaction
- Optimal timing for validation logic

---

## Files in This Solution

| File | Description |
|------|-------------|
| `JOB_COMPRATE_VALIDATION.pcode` | Complete PeopleCode implementation with inline documentation |
| `IMPLEMENTATION_GUIDE.md` | Detailed step-by-step implementation instructions |
| `DATABASE_SETUP.sql` | DDL scripts for creating required tables and sample data |
| `README_COMPRATE_VALIDATION.md` | This file - quick reference and overview |

---

## Quick Start

### 1. Set Up Database Tables

Run the SQL scripts in `DATABASE_SETUP.sql`:

```sql
-- Create salary band configuration table
CREATE TABLE PS_SAL_BAND_CONFIG (...);

-- Create audit/lock table
CREATE TABLE PS_JPM_JP_ITEMS (...);

-- Insert sample configuration data
INSERT INTO PS_SAL_BAND_CONFIG VALUES (...);
```

### 2. Configure Salary Bands

Populate your salary band configuration:

```sql
INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD)
VALUES ('UNION_A', SYSDATE, 150000.00, 50000.00, 'USD');
```

### 3. Add PeopleCode to JOB Component

1. Open PeopleSoft Application Designer
2. Navigate to your JOB component
3. Open the JOB component record
4. Add **SaveEdit** event PeopleCode
5. Copy code from `JOB_COMPRATE_VALIDATION.pcode`
6. **Adjust field names** to match your JOB record structure
7. Save and test

### 4. Test the Validation

Test these scenarios:
- ✅ Salary below maximum → Should save successfully
- ✅ Salary above maximum → Should block save and create JPM_JP_ITEMS record
- ✅ No COMPRATE change → Should not trigger validation
- ✅ Missing config → Should handle gracefully

---

## Key Configuration Points

### Field Name Adjustments

You **must** adjust these field names in the PeopleCode to match your JOB record:

```javascript
// Common variations - check your Application Designer
Local Field &fldComprate = &rs.GetField(Field.COMPRATE);  // or COMP_RATE, ANNUAL_RT, etc.
&labourAgreement = &rs.GetField(Field.LABOUR_AGREEMENT).Value;  // or SAL_ADMIN_PLAN, UNION_CD, etc.
```

### Table Name Adjustments

Adjust table names in SQL queries:

```javascript
// Your config table name
&sqlConfig = CreateSQL("SELECT MAX_SALARY FROM PS_SAL_BAND_CONFIG WHERE ...");

// Your audit table name
&sqlInsert = CreateSQL("INSERT INTO PS_JPM_JP_ITEMS (...) VALUES (...)");
```

---

## Event Comparison

| Event | Best For | Can Block Save? |
|-------|----------|-----------------|
| **SaveEdit** ⭐ | Complex validation, blocking saves | ✅ Yes |
| SavePreChg | Audit logging, can't block save | ❌ No |
| FieldChange | Real-time UI updates | ❌ No |
| FieldEdit | Simple field validation | ⚠️ Field level only |

**Recommendation:** Use **SaveEdit** for this validation.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Changes COMPRATE on JOB Component                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  SaveEdit Event Fires                                        │
│  • Detect change using PriorValue()                          │
│  • Get LABOUR_AGREEMENT from record                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Query PS_SAL_BAND_CONFIG                                    │
│  • Lookup MAX_SALARY for LABOUR_AGREEMENT                    │
│  • Use effective-dated query if applicable                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │  COMPRATE >   │
              │  MAX_SALARY?  │
              └───────┬───────┘
                      │
        ┌─────────────┴─────────────┐
        │ NO                        │ YES
        ▼                           ▼
┌───────────────┐      ┌────────────────────────────┐
│ Allow Save    │      │ Insert JPM_JP_ITEMS record │
│               │      │ • ITEM_TYPE='SRK_OVT_LOCK' │
│               │      │ • Capture context          │
└───────────────┘      └────────────┬───────────────┘
                                    │
                                    ▼
                       ┌────────────────────────────┐
                       │ Display Error Message      │
                       │ Return False (Block Save)  │
                       └────────────────────────────┘
```

---

## Monitoring and Maintenance

### View Pending Violations

```sql
SELECT EMPLID, COMPRATE, MAX_SALARY, LABOUR_AGREEMENT, CREATE_DTTM
FROM PS_JPM_JP_ITEMS
WHERE ITEM_TYPE = 'SRK_OVT_LOCK' AND STATUS = 'N'
ORDER BY CREATE_DTTM DESC;
```

### Update Salary Bands

```sql
-- Add new effective-dated configuration
INSERT INTO PS_SAL_BAND_CONFIG
(LABOUR_AGREEMENT, EFFDT, MAX_SALARY, MIN_SALARY, CURRENCY_CD)
VALUES ('UNION_A', DATE '2025-01-01', 160000.00, 55000.00, 'USD');
```

### Violation Statistics

```sql
SELECT LABOUR_AGREEMENT, COUNT(*) AS VIOLATIONS,
       AVG(COMPRATE - MAX_SALARY) AS AVG_EXCESS
FROM PS_JPM_JP_ITEMS
WHERE ITEM_TYPE = 'SRK_OVT_LOCK' AND STATUS = 'N'
GROUP BY LABOUR_AGREEMENT;
```

---

## Alternative Behaviors

### Option 1: Hard Block (Current Implementation)
- Insert JPM_JP_ITEMS record
- Display error message
- **Return False** to prevent save

### Option 2: Soft Warning
- Insert JPM_JP_ITEMS record
- Display warning message
- **Allow save to continue**

### Option 3: Approval Workflow
- Insert JPM_JP_ITEMS record
- Trigger approval workflow
- Allow save but mark for review

**Adjust the PeopleCode** based on your business requirements.

---

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| "Labour Agreement not found" | Field name mismatch | Verify field name in Application Designer |
| Insert fails | Table structure mismatch | Verify JPM_JP_ITEMS table structure |
| Validation doesn't fire | Wrong event or record | Ensure SaveEdit on Component Record |
| PriorValue() returns null | Field not in buffer | Verify field is on component |

See `IMPLEMENTATION_GUIDE.md` for detailed troubleshooting steps.

---

## Security and Compliance

- ✅ **SQL Injection Protected**: Uses bound parameters (`:1`, `:2`)
- ✅ **Audit Trail**: Complete violation history in JPM_JP_ITEMS
- ✅ **Data Integrity**: Transaction consistency via SaveEdit event
- ✅ **Access Control**: Limit config table updates to HR admins

---

## Performance Considerations

- Single SQL query per save (only when COMPRATE changes)
- Index on PS_SAL_BAND_CONFIG (LABOUR_AGREEMENT, EFFDT)
- Indexes on PS_JPM_JP_ITEMS for reporting queries
- Minimal performance impact on JOB component saves

---

## Support and Documentation

- **Full Implementation Guide**: See `IMPLEMENTATION_GUIDE.md`
- **PeopleCode Source**: See `JOB_COMPRATE_VALIDATION.pcode`
- **Database Scripts**: See `DATABASE_SETUP.sql`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-07 | Initial implementation with SaveEdit event |

---

## License

This PeopleCode solution is provided as-is for use in PeopleSoft implementations.
Adjust and customize based on your specific requirements and naming conventions.

---

**Questions?** Review the detailed `IMPLEMENTATION_GUIDE.md` for comprehensive explanations and examples.
