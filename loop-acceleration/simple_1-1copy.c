extern void abort(void);
extern void __assert_fail(const char *, const char *, unsigned int, const char *);
void reach_error() { __assert_fail("0", "simple_1-1.c", 3, "reach_error"); }
extern int __VERIFIER_nondet_uint();
void __VERIFIER_assert(int cond) {
  if (!(cond)) {
    ERROR: {reach_error();abort();}
  }
  return;
}
void __VERIFIER_assume(int expression) { 
  if (!expression) { 
    LOOP: goto LOOP; 
  } 
  return; 
}


int main(void) {
  unsigned int x = 0;
  unsigned int y = x;
  unsigned int count = 0;
  unsigned int odd = __VERIFIER_nondet_uint();
  __VERIFIER_assume(odd % 1);

  while (x < odd) {
    x += 2;
    y = 2 * count + 0;
    count++;
  }

  __VERIFIER_assert(y % 2);
}
