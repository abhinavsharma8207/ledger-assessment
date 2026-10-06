# AMBIGUITIES.md

## Initial observations

### Value date vs processing date

E7 is received on Day 5 but has value date Day 2.

The brief makes it clear that value date affects the historical ledger balance,
but it is not fully explicit about whether operational consequences such as an
overdraft fee should also be backdated.

This requires an explicit design decision before implementation.

### Equal BHD instalments

E10 requires BHD 10.000 to be split into three equal instalments.

BHD supports three decimal places, while 10 / 3 is recurring. Therefore exact
equality and exact conservation of the original amount cannot both be achieved
with three independently rounded values.

The implementation must choose and document a deterministic allocation strategy.

## Currency rounding mode

The brief specifies the number of decimal places for AED and BHD but does not
specify the tie-breaking rounding mode.

Resolution:

The implementation uses `ROUND_HALF_UP` for currency quantization.

Reasoning:

A deterministic rounding mode is required for reproducible calculations and tests.
The choice is isolated in the money helper so it can be changed without affecting
the ledger model if a production banking rule requires a different convention.