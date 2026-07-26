# Changelog

## P0-04

- Removed the temporary force-flag console print.
- Removed raw analysis-response log dumps.
- Replaced temporary traceback formatting with structured exception logging.
- Added response-length context without exposing response content.
- Added regression tests for silent console behavior and raw-response secrecy.
- Preserved rollback behavior and P0-03 analysis-attempt persistence.
- Marked P0-04 complete and P1-01 next.
- Added automatic backup, install, validation, rollback, and reinstall scripts.
