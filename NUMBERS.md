# NUMBERS.md

All calculations use `Decimal`. AED is rounded to 2 decimal places and BHD to
3 decimal places using `ROUND_HALF_UP`.

Daily interest rate: **0.04% = 0.0004**.

Overdraft fee: **AED 25.00**.

## ACC-001

### Day 1

```text
E1  +1200.00
E2   -950.00
------------
      250.00
```

Closing ledger: **AED 250.00**

Interest:

```text
250.00 * 0.0004 = 0.100 -> AED 0.10
```

### Day 2

E3 creates Auth-A for AED 200.00.

```text
ledger balance    250.00
active hold      -200.00
------------------------
available balance  50.00
```

Auth-A: **APPROVED**.

Interest: **AED 0.10**.

### Day 3

```text
250.00 + 400.00 = 650.00
```

With Auth-A still active:

```text
650.00 - 200.00 = 450.00 available
```

Interest:

```text
650.00 * 0.0004 = 0.260 -> AED 0.26
```

### Day 4

E5 settles Auth-A for AED 185.00:

```text
650.00 - 185.00 = 465.00
```

The settlement is terminal for this exercise, so the unused AED 15.00 hold is
released.

E6 references unknown Auth-Z and is rejected. No AED 180.00 debit is posted.

Interest:

```text
465.00 * 0.0004 = 0.186 -> AED 0.19
```

### Day 5

E7 is booked on Day 5 for AED -620.00 with value date Day 2.

Historical Day-2 balance when evaluated after E7 is known:

```text
250.00 - 620.00 = -370.00
```

Current Day-5 balance before fee:

```text
465.00 - 620.00 = -155.00
```

Auth-B for AED 90.00 is therefore declined.

The implementation assesses the overdraft fee on the processing day on which E7
becomes known:

```text
-155.00 - 25.00 = -180.00
```

Interest: **AED 0.00** because the closing balance is not positive.

### Day 6

E9 appends a compensating +AED 620.00 reversal of E7 with value date Day 2.
E7 remains in the append-only ledger.

```text
-180.00 + 620.00 = 440.00
```

The separately posted overdraft fee is not implicitly reversed.

Day-6 interest before capitalization:

```text
440.00 * 0.0004 = 0.176 -> AED 0.18
```

Rounded daily accruals:

```text
Day 1  0.10
Day 2  0.10
Day 3  0.26
Day 4  0.19
Day 5  0.00
Day 6  0.18
-------------
Total   0.83
```

Single Day-6 interest posting: **+AED 0.83**.

Final ACC-001 balance:

```text
440.00 + 0.83 = AED 440.83
```

## ACC-002

E10 credits BHD 10.000 as three representable instalments.

Three BHD 3.334 instalments would create money:

```text
3.334 * 3 = 10.002
```

Conserving split:

```text
3.334
3.333
3.333
-----
10.000
```

Day-5 interest:

```text
10.000 * 0.0004 = BHD 0.004
```

Day-6 interest before capitalization:

```text
10.000 * 0.0004 = BHD 0.004
```

Capitalized amount:

```text
0.004 + 0.004 = BHD 0.008
```

Final ACC-002 balance:

```text
10.000 + 0.008 = BHD 10.008
```
