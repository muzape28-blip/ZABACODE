# ZMUX + ZABACODE coexistence fix

Same issue as ZABACODE: both on port 5000 caused cross-talk.

Fix:
- Zmux now on 6000, Zabacode on 5000
- Hook injects taskAffinity=com.zaba.zmux + singleTop
- Server binds strictly to 6000

See ZABACODE repo docs/COEXISTENCE_FIX.md for deep dive.
